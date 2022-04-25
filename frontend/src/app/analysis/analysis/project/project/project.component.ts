import { AfterViewInit, Component, ElementRef, EventEmitter, Input, OnInit, Output, ViewChild } from '@angular/core';
import { Prediction, Project } from 'src/api';
import { BehaviorSubject } from 'rxjs';
import { NzTreeFlatDataSource, NzTreeFlattener } from 'ng-zorro-antd/tree-view';
import { FlatTreeControl } from '@angular/cdk/tree';


interface TreeNode {
  name: string;
  key: string;
  hasError?: boolean;
  children?: any[];
  isSample: boolean;
}

interface FlatNode {
  expandable: boolean;
  name: string;
  key: string;
  hasError?: boolean;
  level: number;
  isSample: boolean;
}


@Component({
  selector: 'app-project',
  templateUrl: './project.component.html',
  styleUrls: ['./project.component.less']
})
export class ProjectComponent implements OnInit, AfterViewInit {

  @Input() dragging!: BehaviorSubject<boolean>;
  @Input() prediction: BehaviorSubject<Prediction>;
  @Input() project: Project;

  @Output() addAllSamples = new EventEmitter();

  tree: any[] = [];
  treeControl: FlatTreeControl<FlatNode>;
  treeDataSource: NzTreeFlatDataSource<TreeNode, FlatNode, FlatNode>;

  isSample = (_: number, node: FlatNode): boolean => node.isSample;

  private transformer = (node: TreeNode, level: number): FlatNode => ({
    expandable: !!node.children && node.children.length > 0,
    name: node.name,
    level,
    hasError: node.hasError,
    key: node.key,
    isSample: node.isSample
  });

  constructor(private elementRef: ElementRef) {
  }

  getHeight() {
    return `${this.elementRef.nativeElement.parentElement.offsetHeight - 38}px`;
  }

  ngOnInit(): void {
    this.treeControl = new FlatTreeControl<FlatNode>(
      node => node.level,
      node => node.expandable
    );

    const treeFlattener = new NzTreeFlattener(
      this.transformer,
      node => node.level,
      node => node.expandable,
      node => node.children
    );

    this.treeDataSource = new NzTreeFlatDataSource(this.treeControl, treeFlattener);
    // @ts-ignore bugged
    this.treeControl.trackBy = (node) => node.key;
    this.createTree(this.project);
  }

  ngAfterViewInit(): void {
    this.prediction.subscribe(pred => this.onPrediction(pred));
  }

  onPrediction(pred: Prediction): void {
    this.tree.forEach((el: any) => el.hasError = false);
    pred?.sample_predictions.forEach(sample_prediction => {
      const sample = sample_prediction.sample;
      const preds = sample_prediction.prediction;
      preds.forEach(label => {
        if (label.labelClass.severity === 'warning' || label.labelClass.severity === 'error') {
          this.tree.find((el: any) => el.key === sample.toString()).hasError = true;
        }
      });
    });
    this.treeDataSource.setData(this.tree);
  }

  createTree(project: Project): void {
    for (let i = 0; i < project.samples; i++) {
      if (project.dimensions > 1) {
        const SampleNode: TreeNode = {
          name: `Sample ${i + 1}`,
          key: `${i + 1}`,
          hasError: false,
          children: this.createDimensions(i + 1, project.dimensions),
          isSample: true
        };
        this.tree.push(SampleNode);
      } else {
        const SampleNode: TreeNode = {
          name: `Sample ${i + 1}`,
          key: `${i + 1}`,
          hasError: false,
          isSample: true
        };
        this.tree.push(SampleNode);
      }
    }
  }

  createDimensions(sample: number, dimensions: number): any[] {
    const result: TreeNode[] = [];
    for (let d = 0; d < dimensions; d++) {
      const dimensionNode: TreeNode = {
        name: `Sensor ${d + 1}`,
        key: `${sample}-${d + 1}`,
        isSample: false
      };
      result.push(
        dimensionNode
      );
    }
    return result;
  }

}
