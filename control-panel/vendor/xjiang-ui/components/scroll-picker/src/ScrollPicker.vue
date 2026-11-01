<!-- https://github.com/HJ29/vue3-scroll-picker -->
<script lang="ts">
import {
  computed,
  ComputedRef,
  nextTick,
  onBeforeUnmount,
  onMounted,
  PropType,
  reactive,
  toRefs,
  UnwrapRef,
  watch,
} from "vue";
import { defineComponent } from "vue";

export type SrollPickerSelection = string | number | null;

interface EventElement {
  name: string;
  handler: EventListenerOrEventListenerObject;
}

interface ColumnPane {
  overlay?: HTMLElement;
  content?: HTMLElement;
}

export interface ScrollPickerOption {
  text: string;
  value: string | number;
  unit?: string;
  children?: Array<ScrollPickerOption>;
}

interface HiScrollPickerState {
  self: any;
  timer: any;
  columns: ColumnPane[];
  newOptions: ScrollPickerOption[][];
  markings: number[][];
  events: ComputedRef<EventElement[]>;
  isTouchable: boolean;
  isMouseDown: boolean;
  isScrollingColumnIndex: number | null;
  mouseDownStart: {
    top: number | null;
    y: number | null;
  };
  activeOptionHeight: number;
}

export default defineComponent({
  name: "ScrollPicker",
  props: {
    modelValue: {
      default: [],
      type: Array as PropType<SrollPickerSelection[]>,
    },
    options: {
      default: [],
      type: Array as PropType<ScrollPickerOption[][]>,
    },
    activeClass: {
      default: "",
      type: String,
    },
    inactiveClass: {
      default: "",
      type: String,
    },
    activeStyle: {
      default: "",
      type: String,
    },
    inactiveStyle: {
      default: "",
      type: String,
    },
    wheelSpeed: {
      default: 1,
      type: Number,
    },
  },
  emits: ["update:modelValue"],
  setup(props, { emit }) {
    /***
     * 滚动暂停后，刷新Picker
     * @param options
     * @param columnIndex
     */
    function refreshScrollPicker(options: ScrollPickerOption[][], columnIndex: number = 0) {
      if (options?.length) {
        const curVal = props.modelValue[columnIndex];
        let curIndex = options[columnIndex].findIndex(item => item.value === curVal);
        curIndex = curIndex > -1 ? curIndex : 0;
        const children = options[columnIndex][curIndex].children;
        if (children?.length) {
          options[columnIndex + 1] = children;
          refreshScrollPicker(options, columnIndex + 1);
          const newModelValue = [...props.modelValue];
          if (compareOptions(options, columnIndex + 1)) {
            const oldIndex = children.findIndex(item => getValue(item) === newModelValue[columnIndex + 1]);
            newModelValue[columnIndex + 1] = oldIndex < 0 ? getValue(children[0]) : newModelValue[columnIndex + 1];
          } else {
            newModelValue[columnIndex + 1] = getValue(children[0]);
          }
          setSelections(newModelValue);
        }
        state.newOptions = options;
      }
    }
    function compareOptions(options: ScrollPickerOption[][], endIndex: number) {
      for (let i = 0; i < endIndex; i++) {
        if (JSON.stringify(options) !== JSON.stringify(state.newOptions)) {
          return false;
        }
      }
      return true;
    }
    function getMarkings(columns: ColumnPane[]) {
      return columns.map(column => {
        const rows: number[] = [];
        let y = 0;
        if (column.content) {
          for (let i = 0; i < column.content.children.length; i++) {
            const row = column.content.children[i];
            if (row.id.includes("row-")) {
              rows.push(y);
              y += row.clientHeight;
            }
          }
        }
        return rows;
      });
    }
    function getTouchInfo(event: Event): MouseEvent | Touch {
      const touchEvent = event as TouchEvent;
      return state.isTouchable ? touchEvent.changedTouches[0] || touchEvent.touches[0] : (event as MouseEvent);
    }
    function preventDefault(event: Event) {
      if (event.cancelable) {
        event.preventDefault();
        event.stopPropagation();
      }
    }
    function getContent(event: Event) {
      const index = Number((event.target as HTMLElement).id.replace("column-", ""));
      return state.columns[index].content || null;
    }
    function handleStart(event: Event) {
      preventDefault(event);
      const content = getContent(event);
      const overlay = event.target as HTMLElement;
      const touchInfo = getTouchInfo(event as TouchEvent);
      state.mouseDownStart.y = touchInfo?.clientY || null;
      state.mouseDownStart.top = content?.scrollTop || null;
      if (!state.isTouchable) {
        state.isMouseDown = true;
        if (overlay) overlay.style.cursor = "grabbing";
      }
      const { columnIndex } = getColumnRowIndex(content);
      state.isScrollingColumnIndex = columnIndex;
    }
    function handleMove(event: Event) {
      preventDefault(event);
      const content = getContent(event);
      if (state.isTouchable || state.isMouseDown) {
        const touchInfo = getTouchInfo(event);
        const dy = touchInfo.clientY - (state.mouseDownStart.y || 0);
        if (content) content.scrollTop = (state.mouseDownStart.top || 0) - dy;
      }
      const { columnIndex, rowIndex } = getColumnRowIndex(content);
      const newSelections = getSelections(columnIndex, rowIndex);
      setSelections(newSelections);
    }
    function handleEnd(event: Event) {
      preventDefault(event);
      const content = getContent(event);
      const overlay = event.target as HTMLElement;
      if (!state.isTouchable && state.isMouseDown) {
        state.isMouseDown = false;
        state.mouseDownStart.y = null;
        state.mouseDownStart.top = null;
        if (overlay) overlay.style.cursor = "grab";
      }
      state.isScrollingColumnIndex = null;
      const { columnIndex, rowIndex } = getColumnRowIndex(content);
      const newSelections = getSelections(columnIndex, rowIndex);
      setSelections(newSelections);
      scrollToModelValue(props.modelValue);
    }
    function handleCancel(event: Event) {
      preventDefault(event);
      const content = getContent(event);
      const overlay = event.target as HTMLElement;
      if (!state.isTouchable && state.isMouseDown) {
        state.isMouseDown = false;
        state.mouseDownStart.y = null;
        state.mouseDownStart.top = null;
        if (overlay) overlay.style.cursor = "grab";
      }
      state.isScrollingColumnIndex = null;
      const { columnIndex, rowIndex } = getColumnRowIndex(content);
      const newSelections = getSelections(columnIndex, rowIndex);
      setSelections(newSelections);
      scrollToModelValue(props.modelValue);
    }
    function handleWheel(event: Event) {
      preventDefault(event);
      const content = getContent(event);
      if (content) {
        content.scrollTop += (event as WheelEvent).deltaY * props.wheelSpeed;
        const { columnIndex, rowIndex } = getColumnRowIndex(content);
        const newSelections = getSelections(columnIndex, rowIndex);
        setSelections(newSelections);
        if (state.timer) {
          clearTimeout(state.timer);
          state.timer = null;
        }
        state.timer = setTimeout(() => {
          scrollToModelValue(props.modelValue);
        }, 250);
      }
    }
    function findNearest(arr: number[], value: number) {
      const nearest = arr.reduce(function (prev, curr) {
        return Math.abs(curr - value) < Math.abs(prev - value) ? curr : prev;
      });
      return nearest;
    }
    function getColumnRowIndex(column: HTMLElement | null) {
      if (!column) {
        return {
          columnIndex: null,
          rowIndex: null,
        };
      }
      const columnIndex = Number(column.id.replace("column-", ""));
      const markings = state.markings[columnIndex];
      if (markings?.length > 0) {
        const nearest = findNearest(markings, column.scrollTop);
        const rowIndex = markings.findIndex(v => v === nearest);
        return { columnIndex, rowIndex };
      }
      return {
        columnIndex: null,
        rowIndex: null,
      };
    }
    function modelValueHasChange(newModelValue: SrollPickerSelection[], oldModelValue: SrollPickerSelection[]) {
      if (newModelValue.length !== oldModelValue.length) {
        return true;
      }
      for (let i = 0; i < newModelValue.length; i++) {
        const newValue = newModelValue[i];
        const oldValue = oldModelValue[i];
        if (newValue !== oldValue) {
          return true;
        }
      }
      return false;
    }
    function setSelections(selections: SrollPickerSelection[]) {
      const newSelections = state.newOptions.map((rows, columnIndex) => {
        const selection = selections[columnIndex];
        const rowIndex = rows.findIndex(row => row.value === selection);
        if ((selection === undefined || rowIndex < 0) && rows.length > 0) {
          return getValue(rows[0]);
        }
        return selection;
      });
      const hasChange = modelValueHasChange(newSelections, props.modelValue);
      if (hasChange) {
        emit("update:modelValue", newSelections);
      }
    }
    function getSelections(columnIndex: number | null, rowIndex: number | null) {
      const newModelValue = [...props.modelValue];
      if (typeof columnIndex === "number" && typeof rowIndex === "number") {
        const selection = getValue(state.newOptions[columnIndex][rowIndex]);
        newModelValue[columnIndex] = selection;
      }
      return newModelValue;
    }
    function getEvents(isTouchable: boolean): EventElement[] {
      return [
        {
          name: isTouchable ? "touchstart" : "mousedown",
          handler: handleStart,
        },
        {
          name: isTouchable ? "touchmove" : "mousemove",
          handler: handleMove,
        },
        {
          name: isTouchable ? "touchend" : "mouseup",
          handler: handleEnd,
        },
        {
          name: isTouchable ? "touchcancel" : "mouseleave",
          handler: handleCancel,
        },
        {
          name: "wheel",
          handler: handleWheel,
        },
      ];
    }
    function listenEvent(elements: HTMLElement[]) {
      elements.forEach(element => {
        state.events.forEach(event => {
          element.removeEventListener(event.name, event.handler, false);
          element.addEventListener(event.name, event.handler, false);
        });
      });
    }
    function unlistenEvent(elements: HTMLElement[]) {
      elements.forEach(element => {
        state.events.forEach(event => {
          element.removeEventListener(event.name, event.handler, false);
        });
      });
    }
    function getText(option: ScrollPickerOption | string) {
      return typeof option === "string" ? option : option.text;
    }
    function getValue(option: ScrollPickerOption | string) {
      return typeof option === "string" ? option : option.value;
    }
    function setColumnRef(el: HTMLElement, i: number, type: string) {
      if (el) {
        if (!state.columns[i]) {
          state.columns[i] = {
            content: undefined,
            overlay: undefined,
          };
        }
        if (type === "overlay") {
          state.columns[i].overlay = el;
        }
        if (type === "content") {
          state.columns[i].content = el;
        }
      }
    }
    function filterColumnsContent(columns: ColumnPane[]) {
      return columns.reduce((columns: HTMLElement[], column) => {
        if (column.overlay) {
          columns.push(column.overlay);
        }
        return columns;
      }, []);
    }
    function scrollToModelValue(modelValue: SrollPickerSelection[]) {
      modelValue.forEach((value, columnIndex) => {
        if (columnIndex === state.isScrollingColumnIndex) return;
        nextTick(() => {
          if (state.markings[columnIndex] && value !== undefined) {
            const content = state.columns[columnIndex].content;
            const row = state.newOptions[columnIndex];
            if (content && row) {
              const rowIndex = row.findIndex(row => getValue(row) === value);
              const y = state.markings[columnIndex][rowIndex];
              nextTick(() => {
                content.scrollTo({ top: y, behavior: "smooth" });
              });
            }
          }
        });
      });
    }
    function getIsActive(option: ScrollPickerOption, columnIndex: number) {
      const value = getValue(option);
      return props.modelValue[columnIndex] === value;
    }
    const state: UnwrapRef<HiScrollPickerState> = reactive<HiScrollPickerState>({
      self: null,
      timer: null,
      columns: [],
      newOptions: [],
      markings: [],
      events: computed(() => getEvents(state.isTouchable)),
      isTouchable: false,
      isMouseDown: false,
      isScrollingColumnIndex: null,
      mouseDownStart: {
        top: null,
        y: null,
      },
      activeOptionHeight: 56,
    });
    onMounted(() => {
      state.isTouchable = "ontouchstart" in window || navigator.maxTouchPoints > 0;
      listenEvent(filterColumnsContent(state.columns));
    });
    onBeforeUnmount(() => {
      unlistenEvent(filterColumnsContent(state.columns));
    });
    watch(
      () => state.columns,
      columns => {
        listenEvent(filterColumnsContent(columns));
      },
      { immediate: true, deep: true }
    );
    watch(
      () => props.modelValue,
      async () => {
        nextTick(async () => {
          refreshScrollPicker(JSON.parse(JSON.stringify(props.options)));
          setTimeout(() => {
            state.markings = getMarkings(state.columns);
            scrollToModelValue(props.modelValue);
          }, 2)
        });
      },
      { immediate: true, deep: true }
    );
    watch(
      () => props.options,
      options => {
        state.newOptions = options;
        if (!props.modelValue || props.modelValue.length === 0) {
          setSelections([...new Array(options.length)]);
        }
      },
      { immediate: true, deep: true }
    );
    return {
      ...toRefs(state),
      setColumnRef,
      getText,
      getIsActive,
    };
  },
});
</script>

<template>
  <div class="hi-scroll-picker" ref="self">
    <div class="hi-scroll-picker__center-overlay">
      <slot name="center-overlay">
        <div class="hi-scroll-picker__center-overlay-custom" />
      </slot>
    </div>
    <div class="hi-scroll-picker__pad-top-overlay hi-scroll-picker__pad-overlay hi-scroll-picker__pad">
      <slot name="top-overlay">
        <div class="hi-scroll-picker__pad-top-overlay-custom" />
      </slot>
    </div>
    <div class="hi-scroll-picker__pad-bottom-overlay hi-scroll-picker__pad-overlay hi-scroll-picker__pad">
      <slot name="bottom-overlay">
        <div class="hi-scroll-picker__pad-bottom-overlay-custom" />
      </slot>
    </div>
    <div v-for="(column, i) in newOptions" :key="`column-${i}`" class="hi-scroll-picker__column-container">
      <div class="hi-scroll-picker__column-overlay" :id="`column-${i}`"
        :ref="el => setColumnRef(el as HTMLElement, i, 'overlay')" />
      <div :id="`column-${i}`" class="hi-scroll-picker__column-content"
        :ref="el => setColumnRef(el as HTMLElement, i, 'content')">
        <div class="hi-scroll-picker__pad" />
        <div v-for="(row, j) in column" :key="`row-${j}`" :id="`row-${j}`" class="hi-scroll-picker__row-option"
          :style="getIsActive(row, i) ? activeStyle : inactiveStyle"
          :class="getIsActive(row, i) ? `hi-scroll-picker__row-option--active ${activeClass}` : inactiveClass">
          <slot name="option" :item="row" :active="getIsActive(row, i)">
            <span>
              {{ getText(row) }}
              {{ getIsActive(row, i) && row.unit ? row.unit : "" }}
            </span>
          </slot>
        </div>
        <div class="hi-scroll-picker__pad" />
      </div>
    </div>
  </div>
</template>

<style lang="scss">
.hi-scroll-picker {
  @apply w-full h-[200px] relative flex flex-nowrap justify-center;

  &__column-container {
    @apply relative flex-1;
  }

  &__column-content {
    @apply h-full overflow-y-auto;

    &::-webkit-scrollbar {
      display: none;
    }
  }

  &__column-overlay {
    @apply w-full h-full z-[1] absolute cursor-grab select-none top-0 bottom-0;
  }

  &__row-option {
    @apply h-[36px] text-[14px] flex justify-center items-center;

    span {
      @apply text-[14px];
      color: var(--text-color--first);
    }
  }

  &__row-option--active {
    @apply h-[56px];

    span {
      @apply text-[20px];
      color: var(--active-color);
    }
  }

  &__center-overlay {
    @apply w-full h-[56px] absolute z-[1] top-0 bottom-0 m-auto;
  }

  &__center-overlay-custom {
    @apply h-full border-solid;
    border-width: 1px 0px 1px 0px;
    border-color: var(--separator-color);
  }

  &__pad-overlay {
    @apply absolute z-[1] w-full;
  }

  &__pad-top-overlay {
    @apply top-0;
  }

  &__pad-top-overlay-custom {
    @apply h-full;
    background: linear-gradient(to top, rgba(255, 255, 255, 0), rgba(255, 255, 255, 1));
  }

  &__pad-bottom-overlay {
    @apply bottom-0;
  }

  &__pad-bottom-overlay-custom {
    @apply h-full;
    background: linear-gradient(to bottom, rgba(255, 255, 255, 0), rgba(255, 255, 255, 1));
  }

  &__pad {
    height: calc(50% - 28px);
  }
}

body[data-theme="dark"] {
  .hi-scroll-picker {
    &__pad-top-overlay-custom {
      background: linear-gradient(to top, rgba(0, 0, 0, 0), var(--bg-color__card));
    }

    &__pad-bottom-overlay-custom {
      @apply h-full;
      background: linear-gradient(to bottom, rgba(0, 0, 0, 0), var(--bg-color__card));
    }
  }
}
</style>