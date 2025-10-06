from typing import Any, Self
from dataclasses import dataclass

@dataclass
class SetListItem:
    id: int
    payload: Any

class SetList:
    """ Mantains a list and set of objects 

    -Insert: O(1)
    -Delete: O(1)
    -Get item: O(1)
    -Get list: O(1)
    """

    def __init__(self):
        self._setlist_item_list = []
        self._id_to_index = {}


        self.list = []
        self.id = 0
    

    def append(self, item: Any) -> int:
        self.list.append(item)
        self._setlist_item_list.append(SetListItem(self.id, item))
        self._id_to_index[self.id] = len(self._setlist_item_list) - 1
        self.id += 1
        return self.id - 1
    
    def delete(self, id: int) -> Self:
        if id not in self._id_to_index: return self
        
        # Get data to update last item position after swap
        last_item_id = self._setlist_item_list[-1].id
        deleted_item_index = self._id_to_index[id]

        #Swap items
        i = self._id_to_index[id]
        self.list[i], self.list[-1] = self.list[-1], self.list[i]
        self._setlist_item_list[i], self._setlist_item_list[-1] = self._setlist_item_list[-1], self._setlist_item_list[i]
        
        # Delete item
        self.list.pop()
        self._setlist_item_list.pop()

        # Update id dict
        self._id_to_index[last_item_id] = deleted_item_index
        del self._id_to_index[id]

        return self

    def get_item(self, id: int) -> Any:
        return self.list[self._id_to_index[id]].payload
    
    def __contains__(self, id: int) -> bool:
        return id in self._id_to_index

    def __len__(self) -> int:
        return len(self._setlist_item_list)

    def __iter__(self):
        for item in self._setlist_item_list:
            yield item.payload


