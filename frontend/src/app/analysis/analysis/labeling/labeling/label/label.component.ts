import { Component, Input } from '@angular/core';
import { formatDate } from 'src/app/common/util';
import { Label } from '../../../model/label';

@Component({
  selector: 'app-label',
  templateUrl: './label.component.html',
  styleUrls: ['./label.component.less']
})
export class LabelComponent {

  readonly defaultColor = 'lightgrey';
  readonly formatDate = formatDate;

  @Input() number: number;
  @Input() label: Label;
  @Input() isSelected: boolean;
  @Input() disableTooltip = false;

  constructor() {
  }

}
