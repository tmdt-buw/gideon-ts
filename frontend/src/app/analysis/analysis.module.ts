import { DragDropModule } from '@angular/cdk/drag-drop';
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { SharedModule } from '../shared.module';
import { ANALYSIS_ROUTES } from './analysis.routes';
import { AnalysisComponent } from './analysis/analysis.component';
import { ProjectModule } from './analysis/project/project.module';
import { NgxEchartsModule } from 'ngx-echarts';
import { ChartModule } from './analysis/chart/chart.module';
import { LabelingModule } from './analysis/labeling/labeling.module';
import { ScrollingModule } from '@angular/cdk/scrolling';


@NgModule({
  declarations: [
    AnalysisComponent
  ],
    imports: [
        CommonModule,
        SharedModule,
        RouterModule.forChild(ANALYSIS_ROUTES),
        FormsModule,
        ProjectModule,
        DragDropModule,
        NgxEchartsModule,
        ChartModule,
        LabelingModule,
        ScrollingModule
    ]
})
export class AnalysisModule {
}
