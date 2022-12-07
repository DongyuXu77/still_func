import unittest
from unittest import TestCase

from utils import still

class stillTest(TestCase):
    def test_still_update(self) -> None:
        st = still(delay=1*60, iou_threshold=0.95, pending_delay=10)
        for num in range(100):
            st.update([num], [[num, num, num, num]], num)
            for _, _, idx in st.output_list:
                print(idx)


if __name__=="__main__":
    unittest.main()
