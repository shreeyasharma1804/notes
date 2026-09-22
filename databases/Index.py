'''
store values in the format {index_column_val: ctid}
o(log(n)) retrivel via rebalancing
Best strategy to store on disk:
- Each Tree_Node should be treated as a page of fixed size with a page number
- The parent, left and right pointers should hold a page number instead of the actual pointer
- Serialize all the nodes using the struct module, and append them to a file
- The node can be read using seek(page_number*page_size)
'''

import time
import btreeviz

MAX_ITEMS_PER_NODE = 5

import sys

sys.setrecursionlimit(20)


class Tree_Node:
    def __init__(self) -> None:
        # Ideally should be linked lists for dynamic updates
        self.nodes: list[Data_Node] = []
        self.is_leaf: bool = True
        self.parent: Tree_Node | None = None


class Data_Node:
    def __init__(self, value: dict[int, tuple[int, int]] | int) -> None:
        self.value: dict[int, tuple[int, int]] | int = value
        self.left: Tree_Node | None = None
        self.right: Tree_Node | None = None


class Index:
    def __init__(self) -> None:
        self.root_node: Tree_Node = Tree_Node()

    def _create_data_node(self, value: dict[int, tuple[int, int]] | int) -> Data_Node:
        return Data_Node(value)

    def print_tree(self, current_node: Tree_Node) -> None:
        btreeviz.render_text(current_node)

    def _create_rebalance_node(
        self, current_node: Tree_Node
    ) -> tuple[Data_Node, Tree_Node, Tree_Node]:
        
        # Create the subtree

        rebalance_index: int = MAX_ITEMS_PER_NODE // 2
        try:
            rebalance_node: Data_Node = self._create_data_node(
                next(iter(current_node.nodes[rebalance_index].value.keys())) # type: ignore
            )
        except AttributeError:
            rebalance_node: Data_Node = self._create_data_node(current_node.nodes[rebalance_index].value)
        left_tree_node, right_tree_node = self._split_tree_node(
            current_node, rebalance_index
        )
        rebalance_node.left = left_tree_node
        rebalance_node.right = right_tree_node

        return (rebalance_node, left_tree_node, right_tree_node)

    def _split_tree_node(
        self, current_node: Tree_Node, mid_index: int
    ) -> tuple[Tree_Node, Tree_Node]:
        
        # Create the left and right tree nodes
        # Assign the nodes from current_node to the new tree nodes
        # Define is_leaf
        # parent value is defined by a seperate function

        left_tree_node = Tree_Node()
        right_tree_node = Tree_Node()

        left_tree_node.nodes = current_node.nodes[: mid_index]
        right_tree_node.nodes = current_node.nodes[mid_index:]

        right_tree_node.nodes[0].left = None

        left_tree_node.is_leaf = current_node.is_leaf
        right_tree_node.is_leaf = current_node.is_leaf

        return (left_tree_node, right_tree_node)

    def _assign_parent(
        self,
        parent_node: Tree_Node,
        left_tree_node: Tree_Node,
        right_tree_node: Tree_Node,
    ):
        left_tree_node.parent = parent_node
        right_tree_node.parent = parent_node

        for node in left_tree_node.nodes:
            if node:
                if node.left:
                    node.left.parent = left_tree_node
                if node.right:
                    node.right.parent = left_tree_node

        for node in right_tree_node.nodes:
            if node:
                if node.left:
                    node.left.parent = right_tree_node
                if node.right:
                    node.right.parent = right_tree_node

    def _rebalance_no_parent_node(
        self,
        current_node: Tree_Node,
        left_tree_node: Tree_Node,
        right_tree_node: Tree_Node,
        new_data_node: Data_Node,
    ):

        new_tree_node = Tree_Node()
        new_tree_node.is_leaf = False
        self.root_node = new_tree_node

        new_tree_node.nodes.append(new_data_node)
        self._assign_parent(new_tree_node, left_tree_node, right_tree_node)

        return new_tree_node

    def rebalance(self, current_node: Tree_Node) -> Tree_Node:

        # Create the new data node at the pivot and the left and right tree nodes
        rebalance_node, left_tree_node, right_tree_node = self._create_rebalance_node(
            current_node
        )

        # Check if a parent exists, if yes, attempt insert to the parent tree node
        if current_node.parent:
            parent_node = current_node.parent

            if len(parent_node.nodes) < MAX_ITEMS_PER_NODE:
                # Trivial insert
                self._assign_parent(parent_node, left_tree_node, right_tree_node)

                for i, node in enumerate(parent_node.nodes):
                    if node.value >= rebalance_node.value:
                        parent_node.nodes.insert(i, rebalance_node)
                        node_insert_index = i
                        break
                else:
                    node_insert_index = len(parent_node.nodes)
                    parent_node.nodes.append(rebalance_node)

                if node_insert_index > 0:
                    parent_node.nodes[node_insert_index - 1].right = left_tree_node

                if node_insert_index < len(parent_node.nodes) - 1:
                    parent_node.nodes[node_insert_index + 1].left = right_tree_node

            else:
                return self.rebalance(current_node.parent)

        else:
            # Create a new root node
            return self._rebalance_no_parent_node(
                current_node, left_tree_node, right_tree_node, rebalance_node
            )

        return parent_node

    def insert(
        self, current_node: Tree_Node | None, row_identifier: dict[int, tuple[int, int]]
    ) -> None:

        # Iteratate the tree to reach the correct leaf node

        if not current_node:
            print("Tree Node should not be None")
            return

        row_key = next(iter(row_identifier.keys()))

        if current_node.is_leaf == False:
            for node in current_node.nodes:
                assert isinstance(node.value, int)
                if node.value > row_key:
                    return self.insert(node.left, row_identifier)
            return self.insert(current_node.nodes[-1].right, row_identifier)

        # Tree iteration complete, attemp to insert in the leaf node and trigger a rebalance if required

        # Create the new data node
        data_node: Data_Node = self._create_data_node(row_identifier)

        # Check if trivial insert is possible
        if not current_node.nodes:
            current_node.nodes.append(data_node)

        elif len(current_node.nodes) < MAX_ITEMS_PER_NODE:
            for i, node in enumerate(current_node.nodes):
                assert isinstance(node.value, dict)
                node_key: int = next(iter(node.value.keys()))
                if node_key > row_key:
                    current_node.nodes.insert(i, data_node)
                    break
            else:
                current_node.nodes.append(data_node)

        # Trigger a rebalance and restart tree iteration
        else:
            parent_node = self.rebalance(current_node)
            self.insert(parent_node, row_identifier)

    def delete(self, value: tuple) -> None:
        pass


tuples = (
    {0: (0, 8)},
    {1: (0, 16)},
    {2: (0, 24)},
    {3: (0, 32)},
    {4: (0, 40)},
    {5: (0, 48)},
    {6: (0, 56)},
    {7: {0, 64}},
    {8: {1, 8}},
    {9: {1, 16}},
    {10: {1, 24}},
    {11: {1, 32}},
    {12: {1, 40}},
    {13: {1, 48}},
    {14: {1: 56}},
    {15: {1: 64}},        # 2nd level rebalancing
    {16: {2: 8}},
    {17: {2: 16}},
    {18: {2: 24}},
    {19: {2: 32}},
    {20: {2: 40}},
    {21: {2: 48}},
    {22: {2: 56}},
    {23: {2: 64}},
    {24: {3: 8}},
    {25: {3: 16}},
    {26: {3: 24}},
    {27: {3: 32}},
    {28: {3: 40}},
    {29: {3: 48}},
    {30: {3: 56}},
    {31: {3: 64}},
    {32: {4: 8}},
    {33: {4: 16}},
    {34: {4: 24}},
    {35: {4: 32}},
)

index = Index()

for row in tuples:
    index_root = index.root_node
    index.insert(index_root, row)

index_root = index.root_node
index.print_tree(index_root)
