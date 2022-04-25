export const colors = [
  '#c1232b',
  '#27727b',
  '#fcce10',
  '#e87c25',
  '#b5c334',
  '#fe8463',
  '#9bca63',
  '#fad860',
  '#f3a43b',
  '#60c0dd',
  '#d7504b',
  '#c6e579',
  '#f4e001',
  '#f0805a',
  '#26c0c0'
];

export const initOptions = {renderer: 'svg'};

export const defaultSeries = {
  type: 'line',
  lineStyle: {
    width: 1,
    opacity: 0.8
  },
  showSymbol: false
};

export const defaultBound = {
  type: 'line',
  lineStyle: {
    opacity: 0
  },
  showSymbol: false
};

export const enableBrush = {
  type: 'takeGlobalCursor',
  key: 'brush',
  brushOption: {
    brushType: 'lineX',
    brushMode: 'single'
  }
};

export const disableBrush = {
  type: 'takeGlobalCursor',
  key: 'brush',
  brushOption: {
    brushType: false,
    brushMode: 'single'
  }
};

export const clearBrush = {
  type: 'brush',
  command: 'clear',
  // @ts-ignore
  areas: []
};

export const defaultBrush = {
  brush: {
    brushStyle: {
      color: 'rgba(120,140,180,0.3)'
    }
  }
};

export const coloredBrush = (color: string) => {
  return {
    brush: {
      brushStyle: {
        color,
        opacity: 0.4,
        borderWidth: 3,
        borderColor: color
      }
    }
  };
};

export const addLabelAsBrush = (start: string, end: string) => {
  return {
    type: 'brush',
    areas: [
      {
        brushType: 'lineX',
        coordRange: [start, end],
        xAxisIndex: 0
      }
    ]
  };
};
