import queue


class still:
    r""" The still class gives a method to judge the movement of vehicle using the bbox.
    """
    def __init__(self, delay: int, iou_threshold: float, pending_delay: int=10, drop_last: bool=True) -> None:
        r"""
        Args:
            iou_threshold (float): the  threshold of bbox to arouse movement judging mechanism
            pending_delay (int): the delay frame to compare the bbox of car
            drop_last (bool): whether to drop the data does not compared 

        """
        assert delay>0
        self.delay = delay
        self.delay_queue = queue.Queue(self.delay) # store the length of the items in per update
        self.data_queue = queue.Queue()
        self.info_queue = queue.Queue()
        self.iou_threshold = iou_threshold
        assert pending_delay>0
        self.pending_delay = pending_delay
        self.pending_list :list = [0]*pending_delay
        self.pending_info = list()
        self.pending_data = list()
        self.output_list = list()

    def update(self, idx: list, coordinate: list, data):
        r""" 
        Args:
            coordinate (list): [x1, y1, x2, y2]
            data (any): store the info of each fram   
        """
        self.output_list = list()
        self._update_delay_queue(len(idx), idx, coordinate)

        # add item to queue
        for index in range(len(idx)):
            self.info_queue.put([idx[index], coordinate[index]])
        self.data_queue.put(data)
        
        if len(self.pending_info):
             self._update_pending_list(idx, coordinate)
    
    def _iou(self, list_1, list_2) -> float:
        r""" Intersetion over Union
        """
        [x_1_1, y_1_1, x_1_2, y_1_2] = list_1
        [x_2_1, y_2_1, x_2_2, y_2_2] = list_2
        bb_x1 = max(x_1_1, x_2_1)
        bb_y1 = max(y_1_1, y_2_1)
        bb_x2 = min(x_1_2, x_2_2)
        bb_y2 = min(y_1_2, y_2_2)
        if (bb_x1>bb_x2) or (bb_y1>bb_y2):
            return 0

        Inter = (bb_x2-bb_x1)*(bb_y2-bb_y1)
        Union = (x_1_2-x_1_1)*(y_1_2-y_1_1)+(x_2_2-x_2_1)*(y_2_2-y_2_1)-Inter

        return Inter/Union

    def _judge_iou(self, judge_index: list, ref_index: list, judge_coor: list, ref_coor:list):
        r"""
        Returns:
            return the satisfying judge_index 
        """
        assert len(judge_index)==len(ref_index)
        satisfy_index: list=list()
        for index in range(len(judge_index)):
            num_iou = self._iou(judge_coor[judge_index[index]], ref_coor[ref_index[index]])
            if num_iou < self.iou_threshold:
                satisfy_index.append(judge_index[index])
        return satisfy_index

    def _set_operation(self, list_1: list, list_2: list) -> tuple:
        r"""
        """
        set_1 = set(list_1)
        set_2 = set(list_2)
        set_inter = set_1&set_2
        index_1 = list()  
        index_2 = list()
        for item in set_inter:
            for index in range(len(list_1)):
                if list_1[index] == item:
                    index_1.append(index)
                    break
        for item in set_inter:
            for index in range(len(list_2)):
                if list_2[index] == item:
                    index_2.append(index)
                    break
        return (index_1, index_2)

    def _update_data_queue(self, idx, coordinate):
        r""" put qualified datas to the pending containers and delete others
        """
        judge_idx: list=list()
        judge_coor: list=list()
        while True:
            try:
                [item_id, item_coor] = self.judging_item.get(False)
                judge_idx.append(item_id)
                judge_coor.append(item_coor)
            except queue.Empty:
                break
        judge_index, ref_index = self._set_operation(judge_idx, idx)
        satisfy_list = self._judge_iou(judge_index, ref_index, judge_coor, coordinate)
        count = 0
        data = self.data_queue.get(False)
        for index in range(len(judge_idx)):
            # get the items that satisfy the iou or disappear
            if (index in satisfy_list) or (judge_idx[index] not in idx): 
                self.pending_info.append([judge_idx[index], judge_coor[index]])
                count = count+1
        if count:
            self.pending_data.append(data)
        del data
        self.pending_list = self.pending_list[1:]   # queue-type operation
        self.pending_list.append(count)

    def _update_delay_queue(self, length: int, idx: list, coordinate: list):
        r""" update the delay queue and when delay_queue is full put previous data on self.judging_item
        """
        self.judging_item = queue.Queue()
        if self.delay_queue.full():
            item_num = self.delay_queue.get()
            for _ in range(item_num):
                temp = self.info_queue.get()
                self.judging_item.put(temp)
            self._update_data_queue(idx, coordinate)
        self.delay_queue.put(length)

    def _update_pending_list(self, idx: list, coordinate: list):
        r"""
        """
        left = 0
        for index_1 in range(len(self.pending_list)):
            pending_idx: list = [sub_list[0] for sub_list in self.pending_info[left: self.pending_list[index_1]]]
            pending_coor: list = [sub_list[1] for sub_list in self.pending_info[left: self.pending_list[index_1]]]
            pending_index, ref_index = self._set_operation(pending_idx, idx)
            satisfy_list = self._judge_iou(pending_index, ref_index, pending_coor, coordinate)
            for index_2 in range(len(pending_idx)):
                if (index_2 in pending_index) and (index_2 not in satisfy_list):
                    self.pending_info[left+index_2] = [None, [None]] # drop the data
                    self.call_time = self.call_time+1
            left = self.pending_list[index_1]
        
        if self.pending_list[0]:
            data = self.pending_data[0]
            for index in range(self.pending_list[0]):
                if self.pending_info[index] != [None, [None]]:
                    [idx, coordinate] = self.pending_info[index]
                    self.output_list.append((idx, coordinate, data))
            del data
            self.pending_info = self.pending_info[self.pending_list[0]:]
            self.pending_data = self.pending_data[1:]


