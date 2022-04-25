export class SelectedData {
  id: string;
  color: string;
  sample: number;
  dimension: number;
  disabled: boolean;

  constructor(color: string, sample: number, dimension: number, disabled?: boolean) {
    this.id = `${sample}-${dimension}`;
    this.color = color;
    this.sample = sample;
    this.dimension = dimension;
    this.disabled = disabled || false;
  }

  get label(): string {
    return this.sample === 0 ? `Sensor ${this.dimension}` : `Sample ${this.id}`;
  }

}
