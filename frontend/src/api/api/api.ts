export * from './health.service';
import { HealthService } from './health.service';
export * from './labels.service';
import { LabelsService } from './labels.service';
export * from './projects.service';
import { ProjectsService } from './projects.service';
export * from './timeSeries.service';
import { TimeSeriesService } from './timeSeries.service';
export const APIS = [HealthService, LabelsService, ProjectsService, TimeSeriesService];
