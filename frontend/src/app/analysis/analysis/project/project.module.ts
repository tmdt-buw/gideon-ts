import { DragDropModule } from '@angular/cdk/drag-drop';
import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { SharedModule } from '../../../shared.module';
import { ProjectComponent } from './project/project.component';


@NgModule({
  declarations: [
    ProjectComponent
  ],
  exports: [
    ProjectComponent
  ],
  imports: [
    CommonModule,
    SharedModule,
    FormsModule,
    DragDropModule
  ]
})
export class ProjectModule {
}
