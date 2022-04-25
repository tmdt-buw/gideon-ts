import { Component, EventEmitter, Input, Output } from '@angular/core';
import { Label } from '../../../model/label';
import { BehaviorSubject } from 'rxjs';
import { LabelClass, LabelsService } from '../../../../../../api';
import { formatDate, mapLabelReqToLabel } from '../../../../../common/util';

@Component({
  selector: 'app-selected-label',
  templateUrl: './selected-label.component.html',
  styleUrls: ['./selected-label.component.less']
})
export class SelectedLabelComponent {

  readonly formatDate = formatDate;

  @Input() number: number;
  @Input() label: Label;
  @Input() isSelected: boolean;
  @Input() $labelClasses: BehaviorSubject<LabelClass[]>;

  set labelClasses(labelClasses: LabelClass[]) {
    this.$labelClasses.next(labelClasses);
  }

  get labelClasses(): LabelClass[] {
    return this.$labelClasses.getValue();
  }

  @Output() labelDelete = new EventEmitter();
  @Output() labelChanged = new EventEmitter<Label>();

  constructor(private labelService: LabelsService) {
  }

  updateLabel(): void {
    this.labelService.updateLabel(this.label).subscribe(label => {
      this.label = mapLabelReqToLabel(label, this.labelClasses);
      this.labelChanged.emit(this.label);
    });
  }

  classById(id: string): LabelClass {
    return this.labelClasses.find(cl => cl.id === id);
  }
}
