import { Component, OnDestroy, OnInit } from '@angular/core';
import { FormControl, Validators } from '@angular/forms';
import { NzMessageService } from 'ng-zorro-antd/message';
import { NzUploadChangeParam, NzUploadFile } from 'ng-zorro-antd/upload';
import { catchError, finalize, takeUntil } from 'rxjs/operators';
import { IntegrationStatus, Project, ProjectsService } from '../../../api';
import { environment } from '../../../environments/environment';
import { appRoutesNames } from '../../app.routes.names';
import { of, Subject } from 'rxjs';
import { WebSocketService } from '../../service/websocket.service';

export interface ProjectStatusUpdate {
  id: string;
  progress: number;
  status: IntegrationStatus;
}


@Component({
  selector: 'app-projects',
  templateUrl: './projects.component.html',
  styleUrls: ['./projects.component.less']
})
export class ProjectsComponent implements OnInit, OnDestroy {

  readonly analysisRoute = `/${appRoutesNames.ANALYSIS}`;
  readonly uploadUrl = `${environment.baseUrl}/projects/files`;
  isCreateVisible = false;
  fileList: NzUploadFile[] = [];
  nameControl = new FormControl('', [Validators.required]);

  projects: Project[] = [];
  progress: Map<string, number> = new Map<string, number>();
  loading = false;
  error = false;
  destroyed$ = new Subject();


  constructor(private projectsService: ProjectsService, private message: NzMessageService, private socket: WebSocketService) {
  }

  ngOnInit(): void {
    this.getProjects();
  }

  ngOnDestroy() {
    this.destroyed$.next(null);
  }

  getProjects(): void {
    this.error = false;
    this.loading = true;
    this.projectsService.getProjects().pipe(
      catchError(() => {
        this.error = true;
        return of([]);
      })
    ).subscribe(projects => {
      this.loading = false;
      this.setProjects(projects);
    });
  }

  setProjects(projects: Project[]): void {
    this.projects = projects;
    if (projects.some(project => project.status === IntegrationStatus.Integrating)) {
      this.socket.connect().pipe(
        takeUntil(this.destroyed$)
      ).subscribe((update: ProjectStatusUpdate) => {
        if (update?.status === 'integrating') {
          this.progress.set(update.id, update.progress);
        }
        if (update?.status === 'error') {
          this.projects.find(project => project.id === update.id).status = 'error';
        }
        if (update?.status === 'finished') {
          this.projects.find(project => project.id === update.id).status = 'finished';
        }
      });
    }
  }

  getProgress(project: Project): number {
    return this.progress.get(project.id);
  }

  isIntegrated(project: Project): boolean {
    return project.status === 'finished' || project.status === 'error';
  }

  hasError(project: Project): boolean {
    return project.status === 'error';
  }

  createProject(): void {
    if (this.nameControl.valid && this.fileList.length > 0) {
      this.loading = true;
      this.projectsService.createProject({name: this.nameControl.value, file: this.fileList[0].response}).pipe(
        catchError(() => {
          this.message.error('Could not create project.');
          return of(null);
        }),
        finalize(() => this.loading = false)
      ).subscribe((project) => {
        if (project) {
          this.message.success('Project successfully created.');
          this.close();
          this.getProjects();
        }
      });
    }
  }

  deleteProject(project: Project): void {
    if (project && project.id) {
      this.projectsService.deleteProject(project.id).subscribe(() => this.getProjects());
    }
  }

  close(): void {
    this.fileList = [];
    this.isCreateVisible = false;
    this.nameControl.reset();
  }

  handleChange(info: NzUploadChangeParam): void {
    let fileList = [...info.fileList];
    fileList = fileList.slice(-1);
    fileList = fileList.map(file => {
      if (file.response) {
        file.uuid = file.response;
      }
      return file;
    });
    this.fileList = fileList;
  }

}
