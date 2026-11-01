<script setup lang="ts">
import { computed, onMounted, reactive, shallowRef, watch, watchEffect } from "vue";

import Hotspot from "../hotspot/index.vue";
import Icon from "../icon/index.vue";
import IconButton from "../icon-button/index.vue";

export type CoarseSliderMarks = Array<{
  value: number;
  text: string;
}>;

export type CoarseSliderBreakpoints = number[];

export type CoarseSliderProps = {
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
  icons?: Array<string>;
  containerHeight?: string;
  iconSize?: number;
};

const emits = defineEmits(["change", "complete"]);

const props = withDefaults(defineProps<CoarseSliderProps>(), {
  scale: "auto",
  blockStyle: () => ({}),
  trackStyle: () => ({}),
  showMark: true
});

const [min, max, step] = props.range;
const cslider = shallowRef<HTMLElement>();
const state = reactive({
  percent: 0,
  value: 0,
  sliding: false,
  propChange: false,
  marks: [] as CoarseSliderMarks,
  breakpoints: [] as CoarseSliderBreakpoints,
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

let _percent = state.percent;

let _firstTouch = {
  isFirst: true,
  x: 0
};
const handleSlide = (e: TouchEvent | MouseEvent) => {
  state.sliding = true;
  let newPercent = 0;
  const sliderWidth = cslider.value!.clientWidth;
  const clientX = (e as TouchEvent).touches?.item(0)!.clientX ?? (e as MouseEvent).clientX;

  if (_firstTouch.isFirst) {
    _firstTouch = {
      isFirst: false,
      x: clientX
    }
  }

  newPercent = ((clientX - _firstTouch.x) / sliderWidth) * 100;
  newPercent += _percent
  newPercent = newPercent < 0 ? 0 : newPercent > 100 ? 100 : newPercent;
  if (newPercent === state.percent) return;
  setPercent(newPercent);
};

const handleSlideComplete = () => {
  state.sliding = false;
  _firstTouch = {
    isFirst: true,
    x: 0
  }
};

const handleValueChange = (value: number) => {
  const percent = valueToPercent(value);
  state.percent = percent;
  console.log("handleValueChange---", value)
  state.value = value;
  _percent = state.percent;
  _firstTouch = {
    isFirst: true,
    x: 0
  }
};

const setScale = (scale: CoarseSliderProps["scale"]) => {
  let marks = [] as CoarseSliderMarks,
    breakpoints = [] as CoarseSliderBreakpoints;

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
        const { value, text } = scale[i] as CoarseSliderMarks[number];
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
  <div class="cslider">
    <div class="cslider__button mr-[1.2rem]" v-if="showButton">
      <Hotspot class="flex justify-center items-center w-[3.6rem] h-[3.6rem]" @click="onMinusClick" :disabled="isMinusDisabled">
        <IconButton name="icon-minus" :size="iconSize ?? 3.6" />
      </Hotspot>
    </div>

    <div
      class="cslider__container"
      ref="cslider"
      @mousedown.prevent="handleSlide"
      @mouseup.prevent="handleSlideComplete"
      :style="{
        background: trackColor,
        height: containerHeight
      }"
    >
      <div
        class="cslider__track"
        :style="{
          background: trackTintColor,
        }"
      >
        <div
          :style="{ width: `${ cslider?.clientWidth || 0 }px` }"
          class="relative h-full"
        >
          <div 
            class="cslider__marks-wrapper cslider__marks-wrapper-top" 
            v-if="showMark"
          >
            <div
              class="cslider__mark break-keep"
              v-for="item in state.marks"
              :key="item.value"
              :style="{
                left: `${valueToPercent(item.value)}%`,
                transform: `translateX(${item.value === min ? 0 : item.value === max ? -100 : -50}%)`,
              }"
            >
              {{ `${item.text}${unit || ""}` }}
            </div>
          </div>
          
          <div class="cslider__icons-wrapper cslider__icons-wrapper-top" v-if="icons && icons.length && !showMark">
            <div
              class="cslider__icons break-keep"
              v-for="(item, index) in icons"
              :key="`cslider_icon_${ index }`"
              :style="{ }"
            >
              <Icon :name="item" width="1.2rem" height="1.2rem"  />
            </div>
          </div>
        </div>
      </div>
      <div class="cslider__breakpoints-wrapper">
        <template v-for="item in state.breakpoints" :key="item">
          <div
            v-if="![min, max].includes(item)"
            class="cslider__breakpoint"
            :style="{
              left: `${valueToPercent(item)}%`,
            }"
          ></div>
        </template>
      </div>
      <div class="cslider__marks-wrapper" v-if="showMark">
        <div
          class="cslider__mark break-keep"
          v-for="item in state.marks"
          :key="item.value"
          :style="{
            left: `${valueToPercent(item.value)}%`,
            transform: `translateX(${item.value === min ? 0 : item.value === max ? -100 : -50}%)`,
          }"
        >
          {{ `${item.text}${unit || ""}` }}
        </div>
      </div>
      <div class="cslider__icons-wrapper" v-if="icons && icons.length && !showMark">
        <div
          class="cslider__icons break-keep"
          v-for="(item, index) in icons"
          :key="`cslider_icon_${ index }`"
          :style="{ }"
        >
          <Icon :name="item" width="1.2rem" height="1.2rem"  />
        </div>
      </div>
      <div 
        class="cslider__block-wrapper" 
        @touchmove.prevent="handleSlide" 
        @touchend.prevent="handleSlideComplete"
      >
      </div>
    </div>
    
    <div class="cslider__button ml-[1.2rem]" v-if="showButton">
      <Hotspot class="flex justify-center items-center w-[3.6rem] h-[3.6rem]" @click="onPlusClick" :disabled="isPlusDisabled">
        <IconButton name="icon-plus" :size="iconSize ?? 3.6" />
      </Hotspot>
    </div>
  </div>
</template>

<style lang="scss">
.cslider {
  @apply w-full h-full flex items-center min-h-[3.6rem];
  &__container {
    @apply w-full h-[3.6rem] rounded-full relative overflow-hidden;
    background-color: var(--bg-color__slider);
  }
  &__track {
    @apply h-full absolute overflow-hidden z-10;
    width: v-bind(percentage);
    background-color: var(--active-color);
  }
  &__breakpoint {
    @apply w-[.8rem] h-[.8rem] absolute -translate-x-1/2 z-0;
    background-color: var(--bg-color__slider-breakpoint);
  }
  &__marks-wrapper {
    @apply absolute h-full flex items-center;
    left: 3%; width: 94%;
  }
  &__mark {
    @apply absolute -translate-x-1/2 text-[.8rem];
    color: var(--color-text-second);
  }
  &__marks-wrapper-top{
    z-index: 2;
  }
  &__marks-wrapper-top &__mark {
    color: #fff;
  }

  
  &__icons-wrapper {
    @apply absolute h-full flex justify-between items-center;
    left: 3%; width: 94%;
    color: var(--color-text-second);
  }
  &__icons {
    color: var(--color-text-third);
  }
  &__icons-wrapper-top &__icons {
    color: #fff;
  }

  &__block-wrapper {
    @apply h-full absolute top-[0] right-[0] flex items-center justify-center z-20;
    width: 100%;
  }
  .cslider__button {
    @apply flex justify-center items-center w-[2.6rem] h-[2.6rem];

  }
}
</style>
