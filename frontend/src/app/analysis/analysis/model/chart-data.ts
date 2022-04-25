import { SelectedData } from './selected-data';
import * as uuid from 'uuid';

export class ChartData {
  id: string;
  selectedData: SelectedData[];
  initEvent?: any;

  constructor(initEvent?: any) {
    this.id = uuid.v4();
    this.selectedData = [];
    this.initEvent = initEvent;
  }

}
