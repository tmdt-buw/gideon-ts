import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ChartComponent } from './chart/chart.component';
import { ColorPickerModule } from '@iplab/ngx-color-picker';
import { SharedModule } from '../../../shared.module';
import { NgxEchartsModule } from 'ngx-echarts';
import { DragDropModule } from '@angular/cdk/drag-drop';


@NgModule({
  declarations: [
    ChartComponent
  ],
  exports: [
    ChartComponent
  ],
  imports: [
    CommonModule,
    ColorPickerModule,
    SharedModule,
    NgxEchartsModule,
    DragDropModule
  ]
})
export class ChartModule {
}
