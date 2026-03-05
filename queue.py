class Node[T]:
    def __init__(self, data: T):
        self.data : T = data
        self.next : Node[T] | None = None

class Queue[T]:
    def __init__(self) -> None:
        self.front : Node[T] = None
        self.rear : Node[T] = None
        self.length : int = 0

    def enqueue(self, element) -> None:
        newNode = Node[T](element)
        if self.rear is None:
            self.front = self.rear = newNode
            self.length += 1
            return

        self.rear.next = newNode
        self.rear = newNode
        self.length += 1

    def dequeue(self) -> T | None:
        if self.isEmpty():
            return None
        temp : Node[T] = self.front
        self.front = temp.next
        self.length -= 1
        if self.front is None:
            self.rear = None
        return temp.data

    def peek(self) -> T | None:
        if self.isEmpty():
            return None
        return self.front.data

    def isEmpty(self) -> bool:
        return self.length == 0

    def size(self) -> int:
        return self.length

    def printQueue(self) -> None:
        temp = self.front
        items = []
        while temp:
            items.append(str(temp.data))
            temp = temp.next
        print(" -> ".join(items))
