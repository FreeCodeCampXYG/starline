/** 兼容模板 UI 中热点组件的像素换算；本面板的业务布局不依赖该组件。 */
export const pxToRem = (px: number) => `${px / 16}rem`;
