import { Label as LabelRes, LabelClass } from './../../../../api';

export interface Label extends LabelRes {
  labelClass: LabelClass;
}
