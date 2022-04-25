import { ChangeDetectorRef, Component, ElementRef, HostListener, Input, OnInit, ViewChild } from '@angular/core';
import { NzMessageService } from 'ng-zorro-antd/message';
import { LabelClass, LabelsService, Prediction, PredictionAlgorithm, PredictionRequest, Project, Severity } from '../../../../../api';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { colors, defaultErrorColor, defaultLabelColor, defaultWarningColor } from './labeling.config';
import { groupBy, isNaN } from 'lodash';
import { BehaviorSubject } from 'rxjs';
import { Label } from '../../model/label';
import { NzTreeFlatDataSource, NzTreeFlattener } from 'ng-zorro-antd/tree-view';
import { FlatTreeControl } from '@angular/cdk/tree';
import { finalize } from 'rxjs/operators';

enum LabelSort {
  Time = 'timestamp',
  Label = 'label',
  Sample = 'sample'
}

interface TreeNode {
  name: string;
  sample?: number;
  labelClass?: LabelClass;
  label?: [number, Label];
  children?: TreeNode[];
}

interface FlatNode {
  expandable: boolean;
  name: string;
  level: number;
  sample?: number;
  labelClass?: LabelClass;
  label?: [number, Label];
}


@Component({
  selector: 'app-labeling',
  templateUrl: './labeling.component.html',
  styleUrls: ['./labeling.component.less']
})
export class LabelingComponent implements OnInit {

  @ViewChild('labelList', {read: ElementRef}) labelList: ElementRef;
  @ViewChild('labelTree') labelTree: any;

  // data
  @Input() project: Project;

  // label classes
  @Input() $selectedLabelClass: BehaviorSubject<LabelClass>;
  readonly severities = Severity;
  readonly defaultLabelColor = defaultLabelColor;
  error: string;
  isAddLabelClassModalVisible = false;
  labelClassForm: FormGroup;

  set selectedLabelClass(labelClass: LabelClass) {
    this.$selectedLabelClass.next(labelClass);
  }

  get selectedLabelClass(): LabelClass {
    return this.$selectedLabelClass.getValue();
  }

  // assigned labels
  @Input() $labels: BehaviorSubject<Label[]>;
  @Input() $labelClasses: BehaviorSubject<LabelClass[]>;
  @Input() $hoveredLabel: BehaviorSubject<Label>;
  @Input() $selectedLabel: BehaviorSubject<Label>;
  @Input() $prediction: BehaviorSubject<Prediction>;

  labelPageIndex = 1;
  readonly labelPageSize = 9;
  readonly labelSort = LabelSort;
  readonly predictionAlgorithms = PredictionAlgorithm;
  sort: LabelSort = LabelSort.Time;
  isPredictionLoading = false;
  isPredictionDialogVisible = false;
  predictionForm: FormGroup;

  labelTreeDataSource: NzTreeFlatDataSource<TreeNode, FlatNode, FlatNode>;
  sampleTreeDataSource: NzTreeFlatDataSource<TreeNode, FlatNode, FlatNode>;
  labelTreeControl: FlatTreeControl<FlatNode>;
  sampleTreeControl: FlatTreeControl<FlatNode>;
  isLabelClassNode = (_: number, node: FlatNode): boolean => !!node.labelClass;
  isSampleNode = (_: number, node: FlatNode): boolean => !!node.sample;
  isLabelNode = (_: number, node: FlatNode): boolean => !!node.label;

  readonly sortByTime = (label: Label, other: Label) => label.start - other.start;

  set labels(labels: Label[]) {
    this.$labels.next(labels);
  }

  get labels(): Label[] {
    return this.$labels.getValue();
  }

  get labelsPage(): Label[] {
    const start = (this.labelPageIndex - 1) * this.labelPageSize;
    const end = start + this.labelPageSize;
    return this.$labels.getValue().sort(this.sortByTime).slice(start, end);
  }

  set labelClasses(labelClasses: LabelClass[]) {
    this.$labelClasses.next(labelClasses);
  }

  get labelClasses(): LabelClass[] {
    return this.$labelClasses.getValue();
  }

  set hoveredLabel(label: Label) {
    this.$hoveredLabel.next(label);
  }

  get hoveredLabel(): Label {
    return this.$hoveredLabel.getValue();
  }

  set selectedLabel(selectedLabel: Label) {
    this.$selectedLabel.next(selectedLabel);
  }

  get selectedLabel(): Label {
    return this.$selectedLabel.getValue();
  }

  set prediction(prediction: Prediction) {
    this.$prediction.next(prediction);
  }

  get prediction(): Prediction {
    return this.$prediction.getValue();
  }

  // helper fcts
  unsorted = () => 0;


  constructor(private message: NzMessageService, private labelService: LabelsService, private form: FormBuilder, private change: ChangeDetectorRef) {
  }

  ngOnInit(): void {
    this.resetLabelClassModal();
    this.resetPredictionModal();

    const labelTreeFlattener = new NzTreeFlattener(
      this.transformer,
      node => node.level,
      node => node.expandable,
      node => node.children
    );

    this.labelTreeControl = new FlatTreeControl<FlatNode>(
      node => node.level,
      node => node.expandable
    );
    this.labelTreeDataSource = new NzTreeFlatDataSource(this.labelTreeControl, labelTreeFlattener);
    // @ts-ignore bugged
    this.labelTreeControl.trackBy = (node) => node.name;

    this.sampleTreeControl = new FlatTreeControl<FlatNode>(
      node => node.level,
      node => node.expandable
    );
    this.sampleTreeDataSource = new NzTreeFlatDataSource(this.sampleTreeControl, labelTreeFlattener);
    // @ts-ignore bugged
    this.sampleTreeControl.trackBy = (node) => node.name;

    this.$labels.subscribe(labels => {
      this.labelTreeDataSource.setData(this.labelsTreeByLabel(labels));
      this.sampleTreeDataSource.setData(this.labelsTreeBySample(labels));
    });
  }

  @HostListener('document:keypress', ['$event'])
  handleKeyboardEvent(event: KeyboardEvent) {
    if (!this.isPredictionDialogVisible && !this.isAddLabelClassModalVisible) {
      const key = parseInt(event.key, 10);
      if (!isNaN(key)) {
        this.toggleLabelClass(this.labelClasses[key - 1]);
      }
    }
  }

  openAddLabelDialog() {
    this.resetLabelClassModal();
    this.isAddLabelClassModalVisible = true;
  }

  openPredictionDialog() {
    this.resetPredictionModal();
    this.isPredictionDialogVisible = true;
  }

  createLabelClass() {
    this.error = null;
    this.labelService.createLabelClass(this.project.id, this.getLabelClassWithColor()).subscribe(labelClass => {
      const currentLabelClasses = this.labelClasses;
      currentLabelClasses.push(labelClass);
      this.labelClasses = currentLabelClasses;
      this.isAddLabelClassModalVisible = false;
    }, error => {
      this.error = error.error.detail;
    });
  }

  resetLabelClassModal() {
    this.error = null;
    this.labelClassForm = this.form.group({
      name: ['', [Validators.required]],
      severity: [Severity.Okay]
    });
  }

  resetPredictionModal() {
    this.error = null;
    this.predictionForm = this.form.group({
      algorithm: [PredictionAlgorithm.Dbscan, [Validators.required]],
      window: [500, [Validators.required]],
      eps: [5, [Validators.required]]
    });
  }

  private getLabelClassWithColor(): LabelClass {
    const currentColors = this.labelClasses.map(labelClass => labelClass.color);
    let color;
    const severity = this.labelClassForm.get('severity').value;
    if (severity === Severity.Warning) {
      color = defaultWarningColor;
    } else if (severity === Severity.Error) {
      color = defaultErrorColor;
    } else {
      color = colors.filter((col: string) => !currentColors.includes(col))[0] || colors[0];
    }
    return Object.assign(this.labelClassForm.value, {color});
  }

  toggleLabelClass(label: LabelClass): void {
    if (this.isLabelClassSelected(label)) {
      this.selectedLabelClass = null;
    } else {
      this.selectedLabelClass = label;
    }
  }

  isLabelClassSelected(label: LabelClass): boolean {
    return this.selectedLabelClass === label;
  }

  trackById(index: number, label: LabelClass | Label): string {
    return label.id;
  }

  hoverLabel(label: Label): void {
    if (!this.selectedLabel && label !== this.hoveredLabel) {
      this.hoveredLabel = label;
    }
  }

  unhoverLabel(): void {
    this.hoveredLabel = null;
  }

  isLabelHovered(label: Label): boolean {
    return this.hoveredLabel === label;
  }

  toggleLabel(label: Label): void {
    if (this.isLabelSelected(label)) {
      this.selectedLabel = null;
    } else {
      this.selectedLabel = label;
      this.hoveredLabel = null;
    }
  }

  isLabelSelected(label: Label): boolean {
    return this.selectedLabel === label;
  }

  indexOfLabel(label: Label, index?: number): number {
    if (!index && index !== 0) {
      index = this.labelsPage.indexOf(label);
    }
    return (this.labelPageIndex - 1) * this.labelPageSize + index + 1;
  }

  onLabelChanged(label: Label): void {
    const existingLabel = this.labels.find(lbl => lbl.id === label.id);
    Object.assign(existingLabel, label);
    this.selectedLabel = existingLabel;
  }

  deleteLabel(label: Label): void {
    this.labelService.deleteLabel(label.id).subscribe(() => {
      const labels = this.labels;
      const index = this.labels.indexOf(label);
      labels.splice(index, 1);
      this.labels = labels;
      if (this.selectedLabel === label) {
        this.selectedLabel = null;
      }
    });
  }

  deleteLabelsBySample(event: Event, sampleNode: any) {
    event.stopPropagation();
    const sample = sampleNode.sample;
    this.labelService.deleteLabelsBySample(this.project.id, sample).subscribe(() => {
      this.labels = this.labels.filter(label => label.sample !== sample);
    });
  }

  expandAllNodes(): void {
    if (this.sort === LabelSort.Label) {
      this.labelTreeControl.expandAll();
    }
    if (this.sort === LabelSort.Sample) {
      this.sampleTreeControl.expandAll();
    }
    this.labelTree.changeDetectorRef.detectChanges();
  }

  collapseAllNodes(): void {
    if (this.sort === LabelSort.Label) {
      this.labelTreeControl.collapseAll();
    }
    if (this.sort === LabelSort.Sample) {
      this.sampleTreeControl.collapseAll();
    }
    this.labelTree.changeDetectorRef.detectChanges();
  }

  private labelsTreeByLabel(labels: Label[]): TreeNode[] {
    if (this.labels.length > 0) {
      const grouped = groupBy(labels, (label) => label.label_class);
      return Object.keys(grouped).map(group => {
        const labelClass = this.labelClasses.find(lblClass => lblClass.id === group);
        return {
          name: labelClass.name,
          labelClass,
          children: this.mapLabelsToChildren(grouped[group])
        };
      });
    } else {
      return [];
    }
  }

  private labelsTreeBySample(labels: Label[]): TreeNode[] {
    if (this.labels.length > 0) {
      const grouped = groupBy(labels, (label) => label.sample);
      return Object.keys(grouped).map(group => {
        return {
          name: `Sample ${group}`,
          sample: +group,
          children: this.mapLabelsToChildren(grouped[group])
        };
      });
    } else {
      return [];
    }
  }

  private mapLabelsToChildren(labels: Label[]): TreeNode[] {
    return labels.sort(this.sortByTime).map((label, index) => {
      return {
        name: label.id,
        label: [index, label]
      };
    });
  }

  private transformer = (node: TreeNode, level: number): FlatNode => ({
    expandable: !!node.children && node.children.length > 0,
    name: node.name,
    level,
    sample: node.sample,
    labelClass: node.labelClass,
    label: node.label
  });

  runPrediction(): void {
    this.isPredictionDialogVisible = false;
    this.isPredictionLoading = true;
    const request: PredictionRequest = {
      algorithm: this.predictionForm.get('algorithm').value,
      params: {
        window: this.predictionForm.get('window').value,
        eps: this.predictionForm.get('eps').value
      }
    };
    this.labelService.predictLabels(this.project.id, request).pipe(
      finalize(() => this.isPredictionLoading = false)
    ).subscribe(prediction => this.prediction = prediction);
  }
}

