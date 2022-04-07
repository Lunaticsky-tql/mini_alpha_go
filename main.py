
from copy import deepcopy
import math
import random
from game import Game
from Players import HumanPlayer


class Node:
    def __init__(self, state, parent=None, action=None, color=""):
        self.visits = 0  # 访问次数
        self.reward = 0.0  # 期望值
        self.state = state  # 棋盘状态，Broad类
        self.children = []  # 子节点
        self.parent = parent  # 父节点
        self.action = action  # 从父节点转移到本节点采取的动作
        self.color = color  # 该节点玩家颜色

    # 增加子节点
    def add_child(self, child_state, action, color):
        child_node = Node(child_state, parent=self, action=action, color=color)
        self.children.append(child_node)

    # 判断是否完全展开
    def fully_expand(self):
        action = list(self.state.get_legal_actions(self.color))
        if len(self.children) == len(action):
            return True
        return False


class AIPlayer:
    """
    AI 玩家
    """
    step = 0

    def __init__(self, color):
        """
        玩家初始化
        :param color: 下棋方，'X' - 黑棋，'O' - 白棋
        """
        # 最大迭代次数
        self.max_times = 50
        # 玩家颜色
        self.color = color
        # UCB超参数
        self.SCALAR = 1.2

    def select_expand_node(self, node):
        """
        选择扩展的节点
        :param node: 根节点
        :return: 拓展节点
        """
        while not self.game_overed(node.state):

            if len(node.children) == 0:
                new_node = self.expand(node)
                return new_node
            elif random.uniform(0, 1) < .5:
                node = self.ucb(node, self.SCALAR)
            else:
                node = self.ucb(node, self.SCALAR)
                if not node.fully_expand():
                    return self.expand(node)
                else:
                    node = self.ucb(node, self.SCALAR)
        return node

    def expand(self, node):
        """
        选择扩展的节点
        :param node: 根节点，Node 类
        :return: leave，Node 类
        """
        # 随机选择动作
        action_list = list(node.state.get_legal_actions(node.color))

        if len(action_list) == 0:
            return node.parent

        action = random.choice(action_list)
        tried_action = [child.action for child in node.children]

        # 如果该动作已经被尝试过，则重新选择动作
        while action in tried_action:
            action = random.choice(action_list)

        # 复制状态并根据动作更新到新状态
        new_state = deepcopy(node.state)
        new_state._move(action, node.color)

        # 确定子节点颜色
        if node.color == 'X':
            new_color = 'O'
        else:
            new_color = 'X'

        # 新建节点
        node.add_child(new_state, action=action, color=new_color)
        # 返回所有新拓展的子节点中最后一个
        return node.children[-1]

    def ucb(self, node, scalar):
        """
        选择最佳子节点
        :param node: 节点
        :param scalar: UCT公式超参数
        :return: best_child:最佳子节点
        """
        best_score = -float('inf')
        best_children = []
        for child in node.children:
            exploit = child.reward / child.visits
            if child.visits == 0:
                best_children = [child]
                break
            explore = math.sqrt(2.0 * math.log(node.visits) / float(child.visits))
            now_score = exploit + scalar * explore
            if now_score == best_score:
                best_children.append(child)
            if now_score > best_score:
                best_children = [child]
                best_score = now_score
        if len(best_children) == 0:
            return node.parent
        return random.choice(best_children)

    def act(self, max_times, root):
        """
        根据当前棋盘状态获取最佳落子位置
        :param max_times: 最大搜索次数
        :param root: 根节点
        :return: action 最佳落子位置
        """
        for t in range(max_times):
            leave_node = self.select_expand_node(root)
            reward = self.random_stimulate_chess(leave_node)
            self.backup(leave_node, reward)
            best_child = self.ucb(root, 0)
        return best_child.action

    def random_stimulate_chess(self, node):
        """
        模拟随机对弈
        :param node: 节点
        :return: reward:期望值
        在定义期望值时同时考虑胜负关系和获胜的子数，board.get_winner()会返回胜负关系和获胜子数
        在这里定义获胜积10分，每多赢一个棋子多1分
        reward = 10 + difference
        """
        stimulation_board = deepcopy(node.state)
        color = node.color
        count = 0
        while not self.game_overed(stimulation_board):
            action_list = list(stimulation_board.get_legal_actions(color))
            if not len(action_list) == 0:
                action = random.choice(action_list)
                stimulation_board._move(action, color)
                if color == 'X':
                    color = 'O'
                else:
                    color = 'X'
            else:
                if color == 'X':
                    color = 'O'
                else:
                    color = 'X'
                action_list = list(stimulation_board.get_legal_actions(color))
                action = random.choice(action_list)
                stimulation_board._move(action, color)
                if color == 'X':
                    color = 'O'
                else:
                    color = 'X'
            count = count + 1
            if count >= 200 or self.game_overed(stimulation_board):
                break


        # 价值函数
        winner, difference = stimulation_board.get_winner()
        if winner == 2:
            reward = 0

        elif winner == 1:
            reward = 10 + difference
        else:
            reward = -(10 + difference)

        if self.color == 'X':
            reward = - reward
        print(reward)
        return reward

    def backup(self, node, reward):
        """
        反向传播函数
        """
        while node is not None:
            node.visits += 1
            if node.color == self.color:
                node.reward += reward
            else:
                node.reward -= reward
            node = node.parent
        return 0

    def game_overed(self, state):
        """
        判断游戏是否结束
        """
        # 根据当前棋盘，判断棋局是否终止
        # 如果当前选手没有合法下棋的位子，则切换选手；如果另外一个选手也没有合法的下棋位置，则比赛停止。
        now_loc = list(state.get_legal_actions('X'))
        next_loc = list(state.get_legal_actions('O'))

        over = len(now_loc) == 0 and len(next_loc) == 0  # 返回值 True/False

        return over

    def get_move(self, board):
        """
        根据当前棋盘状态获取最佳落子位置
        :param board: 棋盘
        :return: action 最佳落子位置, e.g. 'A1'
        """
        if self.color == 'X':
            player_name = '黑棋'
        else:
            player_name = '白棋'
        print("请等一会，对方 {}-{} 正在思考中...".format(player_name, self.color))

        board_state = deepcopy(board)
        root = Node(state=board_state, color=self.color)
        action = self.act(50, root)  # 可设置最大搜索次数

        return action


# 人类玩家黑棋初始化
black_player = HumanPlayer("X")

# 随机玩家白棋初始化
white_player = AIPlayer("O")

# 游戏初始化，第一个玩家是黑棋，第二个玩家是白棋
game = Game(black_player, white_player)

# 开始下棋
game.run()