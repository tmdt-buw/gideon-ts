import { Component, EventEmitter, Input, OnDestroy, OnInit, Output } from '@angular/core';
import { CustomSeriesRenderItemAPI, CustomSeriesRenderItemParams, EChartsOption } from 'echarts';
import { SelectedData } from '../../model/selected-data';
import { addLabelAsBrush, clearBrush, coloredBrush, colors, defaultBound, defaultBrush, defaultSeries, disableBrush, enableBrush, initOptions } from './chart.config';
import { CreateLabel, LabelClass, LabelsService, Prediction, PredictionWindow, Project, SamplePrediction, TimeSeries, TimeSeriesProject, TimeSeriesSample, TimeSeriesService } from '../../../../../api';
import { ChartData } from '../../model/chart-data';
import { debounceTime, finalize } from 'rxjs/operators';
import { BehaviorSubject, Subscription } from 'rxjs';
import { Label } from '../../model/label';
import { mapLabelReqToLabel, mapLabelReqToLabels } from '../../../../common/util';
import { groupBy, last, uniq } from 'lodash';

@Component({
  selector: 'app-chart',
  templateUrl: './chart.component.html',
  styleUrls: ['./chart.component.less']
})
export class ChartComponent implements OnInit, OnDestroy {

  readonly initOptions = initOptions;

  @Input() project: Project;

  @Input()
  set chartData(chartData: ChartData) {
    this._chartData = chartData;
  }

  get chartData(): ChartData {
    return this._chartData;
  }

  @Input() isOverviewChart = false;
  @Input() labelClasses: BehaviorSubject<LabelClass[]>;
  @Input() selectedLabelClass: BehaviorSubject<LabelClass>;
  @Input() labels: BehaviorSubject<Label[]>;
  @Input() selectedLabel: BehaviorSubject<Label>;
  @Input() hoveredLabel: BehaviorSubject<Label>;
  @Input() prediction: BehaviorSubject<Prediction>;

  @Output() removeChart = new EventEmitter();

  subscriptions: Subscription[] = [];
  options?: EChartsOption;
  predictions: SamplePrediction[];
  isProcessingPrediction = false;

  private _chartData: ChartData;
  private series: any[] = [];
  private xAxisValues: string[] = [];
  private chart: any;
  private lastDate: Date;
  private _labels: Label[] = [];
  private _selectedLabel = false;
  private highlighted = false;

  dropEnabled = () => !this.isOverviewChart;

  constructor(private tsService: TimeSeriesService, private labelService: LabelsService) {

  }

  ngOnInit(): void {
    this.chartData.selectedData = [];
    this.options = {
      grid: {
        top: '20px',
        left: '40px',
        right: '30px',
        bottom: this.isOverviewChart ? '70px' : '20px'
      },
      xAxis: this.project.hasTimestamps ? {
        type: 'category',
        axisLabel: {
          formatter: (value: number, index: number) => {
            const date = new Date();
            date.setTime(value);
            if (index === 0 || this.lastDate.getDate() !== date.getDate()) {
              this.lastDate = date;
              return `{bold|${date.toLocaleDateString()}}`;
            } else {
              return date.toLocaleTimeString();
            }
          },
          rich: {
            bold: {
              fontWeight: 'bold'
            }
          }
        }
      } : {
        type: 'value'
      },
      yAxis: [{
        type: 'value'
      }
      ],
      dataZoom: [{
        show: this.isOverviewChart,
        labelFormatter: (value: number, valueStr: string) => {
          const date = new Date();
          date.setTime(+valueStr);
          return `${date.toLocaleDateString()}\n\r${date.toLocaleTimeString()}`;
        }
      },
        //   {
        //   type: 'inside',
        //   disabled: this.isOverviewChart,
        //   zoomOnMouseWheel: 'ctrl',
        //   moveOnMouseMove: 'ctrl',
        //   moveOnMouseWheel: 'ctrl',
        //   preventDefaultMouseMove: false
        // }
      ],
      brush: {
        toolbox: ['lineX', 'keep', 'clear'],
        xAxisIndex: 0
      },
      tooltip: {
        trigger: 'axis',
        formatter: (params: any) => this.tooltipFormatter(params)
      },
      toolbox: {
        show: false
      }
    };
  }

  ngOnDestroy(): void {
    this.subscriptions?.forEach(sub => sub?.unsubscribe());
  }

  tooltipFormatter(params: any): string {
    const xAxis = params[0].axisValue;
    const date = new Date();
    date.setTime(+xAxis);
    return date.toLocaleString() + params.map((param: any) => `<br> ${param.value[1]}`);
  }

  setChart(chart: any): void {
    this.chart = chart;
    setTimeout(() => {
      // init data
      const initEvent = this._chartData.initEvent;
      if (initEvent) {
        this.dataDropped(initEvent);
      }
      // register events to enable / disable brush on label class selection
      this.subscriptions.push(
        this.selectedLabelClass?.subscribe(labelClass => {
          if (labelClass) {
            this.chart.dispatchAction(enableBrush);
          } else {
            this.chart.dispatchAction(disableBrush);
          }
        })
      );
      // register brush event for saving and updating labels
      this.chart.on('brushEnd', (brushData: any) => {
        // if not in edit mode
        if (!this.selectedLabel.getValue()) {
          this.drawFinished(brushData);
          this.chart.dispatchAction(clearBrush);
        } else {
          this.updateLabel(brushData);
        }
      });
      this.subscriptions.push(
        // register additional events
        this.labels.subscribe((labels) => {
          let changed = [];
          if (this.isOverviewChart) {
            changed = this.labels.getValue()
              .filter(label => label.dimensions.some(d => !!this.series.find(s => s.enabled && s.dimension === d)))
              .sort((l1, l2) => l1.labelClass.priority - l2.labelClass.priority);
          } else {
            changed = labels
              .filter(label => label !== this.selectedLabel?.getValue() && label.dimensions.some(d => !!this.series.find(s => s.enabled && s.sample === label.sample && s.dimension === d)))
              .sort((l1, l2) => l1.labelClass.priority - l2.labelClass.priority);
          }
          if (changed.length !== this._labels.length) {
            this.updateChart(true, false);
          }
        })
      );
      this.subscriptions.push(
        this.hoveredLabel?.pipe(
          debounceTime(200)
        ).subscribe(label => {
          if (this._labels.includes(label) || this.highlighted) {
            this.highlightLabel(label);
          }
        })
      );
      this.subscriptions.push(
        this.selectedLabel?.subscribe((label: Label) => {
          if (label && this._labels.includes(label)) {
            this.selectedLabelClass?.next(null);
            const selected = this.chartData.selectedData.find(data => !data.disabled && data.sample === label?.sample && label?.dimensions.includes(data.dimension));
            if (selected) {
              this._selectedLabel = true;
              this.chart.setOption(coloredBrush(label.labelClass.color));
              this.updateChart(true, false);
              this.chart.dispatchAction(addLabelAsBrush(label.start.toString(), label.end.toString()));
            }
          } else {
            if (this._selectedLabel) {
              this._selectedLabel = false;
              this.chart.dispatchAction(clearBrush);
              this.chart.setOption(defaultBrush);
              this.updateChart(true, false);
            }
          }
        })
      );
      this.subscriptions.push(
        this.prediction?.subscribe((prediction: Prediction) => {
          if (prediction) {
            this.updateChart(false, true);
          }
        })
      );
    });
  }

  onDataRemove(selectedData: SelectedData): void {
    // remove chart series
    const series = this.series.find(selectedSeries => selectedSeries.id === selectedData.id);
    series.data = null;
    const selectionIndex = this.chartData.selectedData.indexOf(selectedData);
    this.chartData.selectedData.splice(selectionIndex, 1);
    this.updateChart();
    // remove selection
    const index = this.series.indexOf(series);
    this.series.splice(index, 1);
  }

  reset(): void {
    this.series.forEach(ser => ser.data = null);
    this.chartData.selectedData = [];
    this.updateChart();
    this.series = [];
  }

  toggleData(selectedData: SelectedData): void {
    selectedData.disabled = !selectedData.disabled;
    this.updateChart(true, false);
  }

  dataDropped(event: any): void {
    this.chart.showLoading();
    const data: string = event.item.data;

    // project dropped ?
    if (data === this.project.name) {
      this.tsService.getTimeSeries(this.project.id).pipe(
        finalize(() => this.chart.hideLoading())
      ).subscribe((project: TimeSeriesProject) => {
        this.addTimeSeriesProject(project);
      });
    } else {
      const sampleDim = data.split('-');
      const sample = +sampleDim[0];

      // dimension dropped?
      if (sampleDim.length > 1) {
        const dimension = +sampleDim[1];
        this.tsService.getTimeSeriesSampleDimension(this.project.id, sample, dimension).pipe(
          finalize(() => this.chart.hideLoading())
        ).subscribe((ts: TimeSeries) => {
          this.addTimeSeriesDimension(ts, sample, dimension);
          this.updateChart(true, true);
        });

        // sample dropped?
      } else {
        this.tsService.getTimeSeriesSample(this.project.id, sample).pipe(
          finalize(() => this.chart.hideLoading())
        ).subscribe((tsSample: TimeSeriesSample) => {
          this.addTimeSeriesSample(tsSample, sample);
        });
      }
    }
  }

  private addTimeSeriesProject(project: TimeSeriesProject): void {
    project.samples.forEach((tsSample: TimeSeriesSample) => {
      const sample = tsSample.id;
      tsSample.sample.forEach((ts: TimeSeries) => {
        const dimension = ts.id;
        this.addTimeSeriesDimension(ts, sample, dimension);
      });
    });
    this.updateChart(true, true);
  }

  private addTimeSeriesSample(tsSample: TimeSeriesSample, sample: number): void {
    tsSample.sample.forEach((ts: TimeSeries) => {
      this.addTimeSeriesDimension(ts, sample, ts.id);
    });
    this.updateChart(true, true);
  }

  private addTimeSeriesDimension(ts: TimeSeries, sample: number, dimension: number): void {
    if (!this.chartData.selectedData.find(data => data.sample === sample && data.dimension === dimension)) {
      const color = this.nextColor();
      const data = new SelectedData(color, sample, dimension);
      this.updateChartDataFromTimeSeries(data.id, ts, color, sample, dimension);
      this.chartData.selectedData.push(data);
    }
  }

  private updateChartDataFromTimeSeries(id: string, tsSample: TimeSeries, color: string, sample: number, dimension: number): void {
    let isAggregated = false;
    if (tsSample.timestamps) {
      if (tsSample.data_min && tsSample.data_max) {
        isAggregated = true;
        this.series.push(Object.assign({
          id: `L${id}`,
          color,
          stack: id,
          data: tsSample.timestamps.map((v, index) => [v.toString(), tsSample.data_min[index]])
        }, defaultBound));
        this.series.push(Object.assign({
          id: `U${id}`,
          color,
          stack: id,
          areaStyle: {
            color,
            opacity: 0.3
          },
          data: tsSample.timestamps.map((v, index) => [v.toString(), tsSample.data_max[index]])
        }, defaultBound));
      }
      this.series.push(Object.assign({
        id,
        color,
        data: tsSample.timestamps.map((v, index) => [v.toString(), tsSample.data[index]]),
        // set some meta data
        start: tsSample.timestamps[0],
        end: last(tsSample.timestamps),
        sample,
        dimension,
        isAggregated
      }, defaultSeries));
    } else {
      this.series.push(Object.assign({
        id,
        color,
        data: tsSample.data.map((value: number, index: number) => [index, value])
      }, defaultSeries));
    }
  }

  private updateChart(marked: boolean = false, predictions: boolean = false): void {
    if (this.project.hasTimestamps) {
      this.series.sort((series1, series2) => {
        return series1.data[0][0] - series2.data[0][0];
      });
    }
    const series = this.series.map(serie => {
      const selectedData = this.chartData.selectedData.find(selData => selData.id === serie.id.replace('U', '').replace('L', ''));
      if (selectedData?.disabled) {
        // if selection for series is disabled, we add a dummy series without data so that the original series does not change and still holds all the data
        serie.enabled = false;
        const result = Object.assign({}, serie);
        result.data = null;
        result.markArea = null;
        return result;
      }
      // set some meta data - marked areas will be recomputed in the following
      serie.enabled = true;
      if (marked) {
        serie.markArea = null;
      }
      return serie;
    });

    // update x-axis
    this.xAxisValues = uniq(series.flatMap(s => {
      if (s.data) {
        return s.data.map((da: any) => da[0]);
      } else {
        return [];
      }
    }));

    if (series.length > 0) {
      // update marked areas representing none-edited labels
      if (marked) {
        this.updateMarkedAreas(series);
      }
      if (predictions) {
        this.updatePrediction(series);
      }
    }

    this.chart.setOption({
      series,
      xAxis: {
        data: this.xAxisValues
      }
    });
  }

  /**
   * Get next color for new series
   * Will return first color that is not currently used in chart
   * @private
   */
  private nextColor(): string {
    const currentColors = this._chartData.selectedData.map(chartData => chartData.color);
    return colors.filter(col => !currentColors.includes(col))[0] || colors[0];
  }

  private updateLabel(brushData: any): void {
    const range = brushData.areas[0].coordRange;
    const start = +this.xAxisValues[range[0]];
    const end = +this.xAxisValues[range[1]];
    const label = this.selectedLabel.getValue();
    label.start = start;
    label.end = end;
    this.labelService.updateLabel(label).subscribe((labelRes) => {
      const mappedLabel = mapLabelReqToLabel(labelRes, this.labelClasses.getValue());
      const labels = this.labels.getValue();
      const index = labels.findIndex(la => la.id === mappedLabel.id);
      // update label to not break object references
      Object.assign(labels[index], mappedLabel);
      this.labels.next(labels);
    });
  }

  /**
   * Creates label object and send create call to backend when brush ends
   * @param brushData
   * @private
   */
  private drawFinished(brushData: any): void {
    const range = brushData.areas[0].coordRange;
    const start = +this.xAxisValues[range[0]];
    const end = +this.xAxisValues[range[1]];
    const samples = this.series.filter(series => {
      const sampleStart = series.start;
      const sampleEnd = series.end;
      // series starts or ends in label range?
      return series.enabled && !(sampleEnd < start || sampleStart > end);
    }).map(series => series.id);

    // area without series labeled - should never happen
    if (samples.length < 1) {
      console.warn('Invalid label sample');
      return;
    }

    // group by sample for processing of label per sample i.e. all dimensions in one group
    const groupedSamples = groupBy(samples, (sample) => sample.split('-')[0]);

    // create a label for each sample
    const createLabels: CreateLabel[] = [];
    Object.keys(groupedSamples).forEach(sample => {
      const firstSeries = this.series.find(series => series.id.startsWith(sample));
      const sampleStart = firstSeries.start;
      const sampleEnd = firstSeries.end;
      const create: CreateLabel = {
        sample: +sample,
        dimensions: groupedSamples[sample].map(sampleId => sampleId.split('-')[1]),
        label_class: this.selectedLabelClass.getValue().id,
        start: Math.max(sampleStart, start),
        end: Math.min(sampleEnd, end)
      };
      createLabels.push(create);
    });
    this.createLabels(createLabels);
  }

  private createLabels(createLabels: CreateLabel[]): void {
    this.isProcessingPrediction = true;
    // send all create calls to backend and add new labels to behaviour subject
    this.labelService.setLabels(this.project.id, createLabels).pipe(
      finalize(() => this.isProcessingPrediction = false)
    ).subscribe(newLabels => {
      const labels = this.labels.getValue();
      labels.push(...mapLabelReqToLabels(newLabels, this.labelClasses.getValue()));
      this.labels.next(labels);
    });
  }

  private updateMarkedAreas(series: any[]): void {
    if (this.isOverviewChart) {
      const labels = this.labels.getValue()
        .filter(label => label.dimensions.some(d => !!series.find(s => s.enabled && s.dimension === d)))
        .sort((l1, l2) => l1.labelClass.priority - l2.labelClass.priority);
      this._labels = labels;
      this.addLabelsToSeries(series[0], labels);
    } else {
      const labels = this.labels.getValue()
        .filter(label => label !== this.selectedLabel?.getValue() && label.dimensions.some(d => !!series.find(s => s.enabled && s.sample === label.sample && s.dimension === d)))
        .sort((l1, l2) => l1.labelClass.priority - l2.labelClass.priority);
      this._labels = labels;
      const groupBySample = groupBy(labels, (label) => label.sample);
      Object.keys(groupBySample).forEach(sample => {
        const sampleLabels = groupBySample[sample];
        const firstSeries = series.find(serie => serie.sample === +sample);
        this.addLabelsToSeries(firstSeries, sampleLabels);
      });
    }
  }

  private addLabelsToSeries(series: any, labels: Label[]): void {
    const data = [...labels.map(label => {
      return [
        {
          labelId: label.id,
          xAxis: this.findClosestXAxisValue(label.start),
          itemStyle: {
            color: label.labelClass.color,
            opacity: 0.3
          }
        },
        {
          xAxis: this.findClosestXAxisValue(label.end)
        }
      ];
    })];
    series.markArea = {
      silent: true,
      data
    };
  }

  /**
   * Binary search of closest x-Axis value
   * @param timestamp
   * @private
   */
  private findClosestXAxisValue(timestamp: number): string {
    const arr = this.xAxisValues.map(val => +val);
    let from = 0;
    let until = arr.length - 1;
    if (until < 1) {
      console.warn('No x-axis values');
      return '0';
    }
    while (true) {
      const cursor = Math.floor((from + until) / 2);
      if (cursor === from) {
        const diff1 = timestamp - arr[from];
        const diff2 = arr[until] - timestamp;
        return diff1 <= diff2 ? this.xAxisValues[from] : this.xAxisValues[until];
      }
      const found = arr[cursor];
      if (found === timestamp) {
        return this.xAxisValues[cursor];
      }
      if (found > timestamp) {
        until = cursor;
      } else if (found < timestamp) {
        from = cursor;
      }
    }
  }

  private highlightLabel(label?: Label): void {
    this.highlighted = false;
    const labeledSeries = this.series.find(serie => (this.isOverviewChart || serie.sample === label?.sample) && serie.markArea);
    const seriesWithLabels = this.series.filter(serie => serie.markArea);
    seriesWithLabels.forEach(series => {
      const labelArea = labeledSeries?.markArea.data.find((labelData: any) => labelData[0].labelId === label?.id);
      series.markArea.data.forEach((data: any) => {
        if (data === labelArea) {
          data[0].itemStyle.opacity = 0.5;
          this.highlighted = true;
        } else {
          data[0].itemStyle.opacity = 0.3;
        }
      });
    });
    this.chart.setOption({
      series: [
        ...seriesWithLabels
      ]
    });
  }

  acceptPrediction(): void {
    const createLabels: CreateLabel[] = [];
    this.predictions.forEach(prediction => {
      const sample = prediction.sample;
      const preds = prediction.prediction;
      let start = preds[0].start;
      let end = preds[0].end;
      let currentClass = preds[0].labelClass.id;
      for (let i = 1; i < preds.length; i++) {
        const pred = preds[i];
        if (currentClass !== pred.labelClass.id) {
          const createLabel: CreateLabel = {
            sample,
            start,
            end,
            label_class: currentClass,
            dimensions: this.chartData.selectedData.filter(data => !data.disabled && data.sample === sample).map(data => data.dimension)
          };
          createLabels.push(createLabel);
          start = pred.start;
          end = pred.end;
          currentClass = pred.labelClass.id;
        } else {
          end = pred.end;
        }
      }
      const lastLabel: CreateLabel = {
        sample,
        start,
        end,
        label_class: currentClass,
        dimensions: this.chartData.selectedData.filter(data => !data.disabled && data.sample === sample).map(data => data.dimension)
      };
      createLabels.push(lastLabel);
    });
    this.createLabels(createLabels);
  }

  private updatePrediction(series: any[]): void {
    const prediction = this.prediction?.getValue();
    if (prediction) {
      const samples = [...new Set(series.map(serie => serie.sample))];
      if (samples.length > 0) {
        this.predictions = this.isOverviewChart ? prediction.sample_predictions : prediction.sample_predictions.filter((pred: SamplePrediction) => samples.includes(pred.sample));
        const data = this.predictions.flatMap(sPred => sPred.prediction.map((pred: any) => [pred]));
        const custom = {
          type: 'custom',
          renderItem: (param: CustomSeriesRenderItemParams, api: CustomSeriesRenderItemAPI) => {
            // @ts-ignore
            const samplePrediction = api.value(0) as PredictionWindow;
            const startCoord = this.findClosestXAxisValue(samplePrediction.start);
            const endCoord = this.findClosestXAxisValue(samplePrediction.end);
            const start = api.coord([startCoord, 0]);
            const end = api.coord([endCoord, 0]);
            return {
              type: 'rect',
              shape: {
                x: start[0], y: 0, width: end[0] - start[0], height: 15
              },
              style: {
                opacity: 0.4,
                fill: samplePrediction.labelClass.color
              }
            };
          },
          data
        };
        series.push(custom);
      }
    }
  }
}
