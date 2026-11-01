<script setup lang="ts">
import { useAttrs } from "vue";
import XJTitle from "../xj-title/index.vue";
import IconButton from "../icon-button/index.vue";
import Icon from "../icon/index.vue";
import XJSwitch from "../switch/index.vue";

const FunctionCardType = {
  ITEM: "ITEM",
  SWITCH: "SWITCH",
  BUTTON: "BUTTON"
};
export type FunctionCardProps = {
  text: string;
  subtext?: string;
  icon?: string;
  size?: number;
  iconSize?: number;
  active?: boolean;
  disabled?: boolean;
  value?: string | number | boolean;
  showArrow?: boolean;
  type?: string;
  isCard?: boolean;

  button?: {
    text: string;
  } 
};

let MouseTimer: NodeJS.Timeout;
let isLongClick: boolean = false;
const emits = defineEmits(["click", "longclick", "leftclick"]);
const _attrs: any = useAttrs();

const props = withDefaults(defineProps<FunctionCardProps>(), {
  isCard: true,
  type: "ITEM"
});
// const onLongClick: () => void = _attrs?.onLongClick;

const _onClick = () => {
  if (props.disabled) return;
  emits("click");
};
const _onLongClick = () => {
  if (props.disabled) return;
  emits("longclick");
  // onLongClick();
};
const onDown = () => {
  isLongClick = false;
  MouseTimer && clearTimeout(MouseTimer);
  MouseTimer = setTimeout(() => {
    console.log("长按事件");
    isLongClick = true;
  }, 800)
}
const onUp = () => {
  MouseTimer && clearTimeout(MouseTimer);
  if (isLongClick) {
    _onLongClick()
  } else {
    _onClick()
  }
}

const _onLeftClick = () => {
  if (props.disabled) return;
  emits("leftclick");
}
</script>

<template>
  <div 
    :class="{ 'card': isCard, 'cardDisabled': disabled }"
    class="functionCard"
    @mousedown="type === FunctionCardType.SWITCH ? null : onDown()" 
    @mouseup="type === FunctionCardType.SWITCH ? null : onUp()"
    onselectstart="return false;"
  >
    <div class="flex flex-row flex-1 pr-[5px]"
      @click="_onLeftClick"
    >
      <IconButton v-if="icon" :name="icon" :active="active" :size="size" :iconSize="iconSize" />
      <div class="flex flex-col justify-center" :class="{ 'ml-[10px]': icon }">
        <XJTitle :text="text" />
        <span v-if="subtext" class="text-third">{{ subtext }}</span>
      </div>
    </div>
    
    <div
      v-if="type === FunctionCardType.SWITCH"
      @click.stop
    >
      <XJSwitch
        :disabled="disabled"
        :active="!!value"
        @click="_onClick"
      />
    </div>
    <button v-else-if="type === FunctionCardType.BUTTON && button?.text" @click.stop="() => _onClick()">{{button?.text}}</button>
    <span v-else-if="typeof value === 'number' || typeof value === 'string'" class="text-second">{{ value }}</span>
    <Icon v-if="showArrow" name="icon-arrowright" width="1.3rem" height="1.3rem" color="var(--icon-color)" />
  </div>
</template>

<style lang="scss">
.functionCard {
  @apply flex flex-1 items-center;
  min-height: 5rem;

  button {
    width: 4rem;
    height: 2rem;
    border-radius: 2rem;
    border: 1px solid rgb(255, 81, 0);
    background-color: rgb(255, 81, 0, .05);
    color: rgb(255, 81, 0);
  }
}
</style>
