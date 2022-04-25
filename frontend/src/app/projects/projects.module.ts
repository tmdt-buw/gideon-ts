import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { SharedModule } from '../shared.module';
import { PROJECTS_ROUTES } from './projects.routes';
import { ProjectsComponent } from './projects/projects.component';


@NgModule({
  declarations: [
    ProjectsComponent
  ],
    imports: [
        CommonModule,
        SharedModule,
        RouterModule.forChild(PROJECTS_ROUTES),
        ReactiveFormsModule
    ]
})
export class ProjectsModule {
}
