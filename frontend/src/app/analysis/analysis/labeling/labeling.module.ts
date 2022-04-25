import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LabelingComponent } from './labeling/labeling.component';
import { SharedModule } from '../../../shared.module';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { LabelComponent } from './labeling/label/label.component';
import { SelectedLabelComponent } from './labeling/selected-label/selected-label.component';


@NgModule({
  declarations: [
    LabelingComponent,
    LabelComponent,
    SelectedLabelComponent
  ],
  exports: [
    LabelingComponent
  ],
  imports: [
    CommonModule,
    SharedModule,
    FormsModule,
    ReactiveFormsModule
  ]
})
export class LabelingModule {
}
