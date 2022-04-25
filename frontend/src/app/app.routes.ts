import { Routes } from '@angular/router';
import { appRoutesNames } from './app.routes.names';

export const APP_ROUTES: Routes = [
  {path: '', redirectTo: appRoutesNames.PROJECTS, pathMatch: 'full'},
  {path: appRoutesNames.PROJECTS, loadChildren: () => import('./projects/projects.module').then(m => m.ProjectsModule)},
  {path: appRoutesNames.ANALYSIS, loadChildren: () => import('./analysis/analysis.module').then(m => m.AnalysisModule)}
];
