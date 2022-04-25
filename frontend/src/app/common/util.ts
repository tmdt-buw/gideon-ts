import { Label as LabelReq, LabelClass } from './../../api';
import { Label } from '../analysis/analysis/model/label';

export function mapLabelReqToLabels(labels: LabelReq[], labelClasses: LabelClass[]): Label[] {
  return labels.map(label => mapLabelReqToLabel(label, labelClasses));
}

export function mapLabelReqToLabel(label: LabelReq, labelClasses: LabelClass[]): Label {
  const temp = label as Label;
  temp.labelClass = labelClasses.find(labelClass => labelClass.id === label.label_class);
  return temp;
}

export function formatDate(timestamp: number): string {
  const date = new Date();
  date.setTime(timestamp);
  return date.toISOString().replace('T', ' ').replace('Z', '');
}
