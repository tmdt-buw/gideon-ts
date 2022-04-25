import { AfterViewInit, Component, ElementRef, HostListener, OnInit, QueryList, ViewChild, ViewChildren } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { LabelClass, LabelsService, Prediction, Project, ProjectsService, TimeSeriesService } from '../../../api';
import { BehaviorSubject } from 'rxjs';
import { ChartData } from './model/chart-data';
import packageInfo from '../../../../package.json';
import { Label } from './model/label';
import { mapLabelReqToLabels } from '../../common/util';
import { ChartComponent } from './chart/chart/chart.component';
import { delay } from 'rxjs/operators';
import { LabelingComponent } from './labeling/labeling/labeling.component';
import { times } from 'lodash';
import { animate, state, style, transition, trigger } from '@angular/animations';

@Component({
  selector: 'app-analysis',
  templateUrl: './analysis.component.html',
  styleUrls: ['./analysis.component.less'],
  animations: [
    trigger('collapsed', [
      state('false', style({
        opacity: 1,
        width: '*',
        flex: '0 0 100%'
      })),
      state('true', style({
        opacity: 0,
        width: 0,
        flex: 'unset'
      })),
      transition('false <=> true', animate(200))
    ])
  ]
})
export class AnalysisComponent implements OnInit, AfterViewInit {

  @ViewChildren(ChartComponent, {read: ElementRef}) chartViews: QueryList<ChartComponent>;
  @ViewChild(LabelingComponent) labelingComponent: LabelingComponent;

  readonly version = packageInfo.version === '0.0.0' ? 'Development Version' : packageInfo.version;

  // side menus
  isProjectCollapsed = false;
  isLabelsCollapsed = false;

  // data
  project: Project;

  // charts
  charts: ChartComponent[];
  overviewChart?: ChartData;
  _chartData: BehaviorSubject<ChartData[]> = new BehaviorSubject<ChartData[]>([]);
  $dragging = new BehaviorSubject<boolean>(false);

  set chartData(chartData: ChartData[]) {
    this._chartData.next(chartData);
  }

  get chartData(): ChartData[] {
    return this._chartData.getValue();
  }

  // labeling
  selectedLabelClass = new BehaviorSubject<LabelClass>(null);
  labelClasses = new BehaviorSubject<LabelClass[]>([]);
  labels = new BehaviorSubject<Label[]>([]);
  hoveredLabel = new BehaviorSubject<Label>(null);
  selectedLabel = new BehaviorSubject<Label>(null);

  // prediction
  prediction = new BehaviorSubject<Prediction>(null);

  isLabelSelected: boolean;

  constructor(private route: ActivatedRoute, private projectsService: ProjectsService, private tsService: TimeSeriesService, private labelService: LabelsService) {
  }

  @HostListener('window:click', ['$event'])
  onGlobalClick(event: PointerEvent): void {
    if (this.isLabelSelected) {
      // @ts-ignore
      const allowedElements = this.charts.map(chart => chart.nativeElement);
      allowedElements.push(this.labelingComponent.labelList.nativeElement);
      // @ts-ignore
      const clickAllowed = !!allowedElements.find(chartElement => event.path.includes(chartElement));
      if (!clickAllowed) {
        // clear selection if clicked somewhere else than a chart
        this.selectedLabel.next(null);
      }
    }
  }

  ngOnInit(): void {
    this.route.params.subscribe(params => {
      const projectId = params.id;
      this.projectsService.getProject(projectId).subscribe(project => {
        this.project = project;
        this.overviewChart = new ChartData({
          item: {
            data: project.name
          }
        });
      });
      this.labelService.getLabelClasses(projectId).subscribe(labelClasses => {
        this.labelClasses.next(labelClasses);
        this.labelService.getLabels(projectId).subscribe(labels => this.labels.next(mapLabelReqToLabels(labels, labelClasses)));
      });
    });
    // separate var need because of run-conditions
    this.selectedLabel.pipe(delay(1)).subscribe(label => {
      this.isLabelSelected = !!label;
    });
  }

  ngAfterViewInit() {
    this.chartViews.changes.subscribe(charts => this.charts = charts.toArray());
  }

  addChart(index: number, event: any): void {
    this.chartData.splice(index, 0, new ChartData(event));
    this.chartData = [...this.chartData];
  }

  addAllCharts(): void {
    times(this.project.samples, i => this.addChart(i, {
      item: {
        data: (i + 1).toString()
      }
    }));
  }

  addAllChartsWithErrors(): void {
    const errorIds = this.prediction.getValue().sample_predictions.filter(samplePred => samplePred.prediction.some(pred => pred.labelClass.severity === 'warning' || pred.labelClass.severity === 'error')).map(pred => pred.sample);
    errorIds.forEach(id => {
      this.addChart(id, {
        item: {
          data: id.toString()
        }
      })
    })
  }

  onRemoveChart(index: number): void {
    this.chartData.splice(index, 1);
    this.chartData = [...this.chartData];
  }

  onRemoveAllCharts(): void {
    this.chartData = [];
  }

  trackById(index: number, chartData: ChartData): string {
    return chartData.id;
  }
}
