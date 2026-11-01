<script setup lang="ts">
import { computed, onMounted, reactive, shallowRef, watch, watchEffect } from "vue";

import Hotspot from "../hotspot/index.vue";
import Icon from "../icon/index.vue";
import IconButton from "../icon-button/index.vue";

export type SliderMarks = Array<{
  value: number;
  text: string;
}>;

export type SliderBreakpoints = number[];

export type SliderProps = {
  value: number;
  unit?: string | null;
  range: [number, number, number];
  scale?:
  | "auto"
  | number[]
  | Array<{
    value: number;
    text: string;
  }>
  | null;
  blockStyle?: {
    backgroundColor?: string;
    background?: string;
    borderColor?: string;
  };
  trackColor?: string;
  trackTintColor?: string;
  showButton?: boolean;
  showMark?: boolean;
};

const emits = defineEmits(["change", "complete"]);

const props = withDefaults(defineProps<SliderProps>(), {
  scale: "auto",
  blockStyle: () => ({}),
  trackStyle: () => ({}),
  showMark: true
});

const [min, max, step] = props.range;
const slider = shallowRef<HTMLElement>();
const state = reactive({
  percent: 0,
  value: 0,
  sliding: false,
  propChange: false,
  marks: [] as SliderMarks,
  breakpoints: [] as SliderBreakpoints,
});

const percentage = computed(() => `${state.percent}%`);
const isMinusDisabled = computed(() => state.value <= min);
const isPlusDisabled = computed(() => state.value >= max);

const valueToPercent = (value: number) => {
  const lengthPerStep = 100 / ((max - min) / step);
  const percent = Math.round((value - min) / step * lengthPerStep);
  return percent > 100 ? 100 : percent < 0 ? 0 : percent;
};

const setPercent = (percent: number) => {
  const lengthPerStep = 100 / ((max - min) / step);
  const steps = Math.round(percent / lengthPerStep);
  const newPercent = (steps * lengthPerStep);
  const newValue = Math.round(((steps * lengthPerStep * (max - min) * 0.01) * 1000 + min * 1000) / 1000);
  // const newValue = steps * lengthPerStep * (max.value - min.value) * 0.01 + min.value;
  state.percent = newPercent;
  state.value = newValue;
};

const handleSlide = (e: TouchEvent | MouseEvent) => {
  state.sliding = true;
  let newPercent = 0;
  const sliderWidth = slider.value!.clientWidth;
  const clientX = (e as TouchEvent).touches?.item(0)!.clientX ?? (e as MouseEvent).clientX;
  const sliderOffsetLeft = slider.value!.getBoundingClientRect().left;
  newPercent = ((clientX - sliderOffsetLeft) / sliderWidth) * 100;
  newPercent = newPercent < 0 ? 0 : newPercent > 100 ? 100 : newPercent;
  if (newPercent === state.percent) return;
  setPercent(newPercent);
};

const handleSlideComplete = () => {
  state.sliding = false;
};

const handleValueChange = (value: number) => {
  console.log("handleValueChange---", value)
  const percent = valueToPercent(value);
  state.percent = percent;
  console.log("handleValueChange---", value, percent)
  state.value = value;
};

const setScale = (scale: SliderProps["scale"]) => {
  let marks = [] as SliderMarks,
    breakpoints = [] as SliderBreakpoints;

  if (!scale) {
    return;
  } else if (scale === "auto") {
    marks = [
      { value: min, text: `${min}` },
      { value: max, text: `${max}` },
    ];
    breakpoints = [min, max];
  } else {
    for (let i = 0; i < scale.length; i++) {
      if (typeof scale[i] === "number") {
        const value = scale[i] as number;
        marks.push({
          value,
          text: `${value}`,
        });
        breakpoints.push(value);
      } else {
        const { value, text } = scale[i] as SliderMarks[number];
        marks.push({
          value,
          text,
        });
        breakpoints.push(value);
      }
    }
  }

  state.marks = marks;
  state.breakpoints = breakpoints;
};

const onMinusClick = () => {
  if (isMinusDisabled.value) return;
  let newValue = state.value - step;
  if (newValue <= min) {
    newValue = min;
  }
  handleValueChange(newValue);
};

const onPlusClick = () => {
  if (isPlusDisabled.value) return;
  let newValue = state.value + step;
  if (newValue >= max) {
    newValue = max;
  }
  handleValueChange(newValue);
};

watch([() => state.sliding, () => state.value], ([sliding, value]) => {
  if (state.propChange) {
    emits("change", value);
    state.propChange = false;
    return;
  }
  // if (value === props.value) return;
  if (sliding) {
    emits("change", value);
  } else {
    emits("complete", value);
  }
});

watch(
  () => props.value,
  value => {
    if (state.sliding) return;
    state.propChange = true;
    handleValueChange(value);
  },
  {
    immediate: true,
  }
);

onMounted(() => {
  watchEffect(() => {
    setScale(props.scale);
  });
});
</script>

<template>
  <div class="hi-slider">
    <div class="hi-silder__button mr-[1.2rem]" v-if="showButton">
      <Hotspot class="flex justify-center items-center w-[2.6rem] h-[2.6rem]" @click="onMinusClick"
        :disabled="isMinusDisabled">
        <IconButton name="ic_I_minus" :active="true" :size="2.6" />
      </Hotspot>
    </div>

    <div class="hi-slider__container" ref="slider" @mousedown.prevent="handleSlide"
      @mouseup.prevent="handleSlideComplete" :style="{
        background: trackColor,
      }">
      <div class="hi-slider__track" :style="{
        background: trackTintColor,
      }"></div>
      <div class="hi-slider__breakpoints-wrapper">
        <template v-for="item in state.breakpoints" :key="item">
          <div v-if="![min, max].includes(item)" class="hi-slider__breakpoint" :style="{
            left: `${valueToPercent(item)}%`,
          }"></div>
        </template>
      </div>
      <div class="hi-slider__marks-wrapper" v-if="showMark">
        <div class="hi-slider__mark break-keep" v-for="item in state.marks" :key="item.value" :style="{
          left: `${valueToPercent(item.value)}%`,
          transform: `translateX(${item.value === min ? 0 : item.value === max ? -100 : -50}%)`,
        }">
          {{ `${item.text}${unit || ""}` }}
        </div>
      </div>
      <div class="hi-slider__block-wrapper" @touchmove.prevent="handleSlide" @touchend.prevent="handleSlideComplete">
        <div class="hi-slider__block" :style="blockStyle"></div>
      </div>
    </div>

    <div class="hi-silder__button ml-[1.2rem]" v-if="showButton">
      <Hotspot class="flex justify-center items-center w-[2.6rem] h-[2.6rem]" @click="onPlusClick"
        :disabled="isPlusDisabled">
        <IconButton name="ic_I_plus" :active="true" :size="2.6" />
      </Hotspot>
    </div>
  </div>
</template>

<style lang="scss">
.hi-slider {
  @apply w-full h-full flex items-center min-h-[3.2rem];

  &__container {
    @apply w-full h-[.8rem] rounded-full relative;
    background-color: var(--bg-color__slider);
  }

  &__track {
    @apply h-full rounded-full absolute overflow-hidden z-10;
    width: v-bind(percentage);
    background-color: var(--active-color);
  }

  &__breakpoint {
    @apply w-[.8rem] h-[.8rem] absolute -translate-x-1/2 z-0;
    background-color: var(--bg-color__slider-breakpoint);
  }

  &__mark {
    @apply absolute -translate-x-1/2 text-[.8rem] top-[1.3rem];
    color: var(--color-text-second);
  }

  &__block-wrapper {
    @apply w-[3rem] h-[3rem] absolute -translate-x-1/2 -top-[1.1rem] flex items-center justify-center z-20;
    left: v-bind(percentage);
  }

  &__block {
    @apply w-[1.6rem] h-[1.6rem] rounded-full bg-white;
    border: 0.5px solid rgba(0, 0, 0, 0.04);
    box-shadow:
      0 0 1px rgba(0, 0, 0, 0.15),
      0 0 2px rgba(0, 0, 0, 0.15);
  }

  .hi-slider__button {
    @apply flex justify-center items-center w-[2.6rem] h-[2.6rem];

  }
}
</style>
