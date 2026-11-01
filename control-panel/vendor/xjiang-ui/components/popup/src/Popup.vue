<!-- eslint-disable vue/multi-word-component-names -->
<script setup lang="ts">
import { type VNode, onMounted, ref, defineComponent, reactive } from "vue";
import i18n from "../../../i18n";
import { ScrollPickerOption, SrollPickerSelection } from "../../scroll-picker/src/ScrollPicker.vue";
import ScrollPicker from "../../scroll-picker";
import XJInput from "../../input";
import { XJInputProps } from "../../input/src/XJInput.vue";

export type DialogButton = {
  text?: string;
  color?: string;
  onClick?: (...result: any[]) => boolean;
};

export type HiDialogRadioOptions = {
  text?: string;
  color?: string;
  value?: string;
  onClick?: (...result: any[]) => boolean;
};

export interface PopupProps {
  type: "loading" | "dialog" | "dialog-custom" | "dialog-scroll-picker" | "dialog-input";
  id: string;
  text?: string;
  title?: string;
  subtitle?: string;
  canDismiss?: boolean;
  onClose?: () => void;
  leftButton?: DialogButton;
  rightButton?: DialogButton;
  showRightButton?: boolean;
  customNode?: VNode | null;
  scrollPickerOptions?: ScrollPickerOption[][];
  scrollPickerSelections?: SrollPickerSelection[];
  radioPickerOptions?: HiDialogRadioOptions[];
  inputOptions?: XJInputProps;
}

const { tm } = i18n.global;

const emits = defineEmits(["close", "destroy", "error"]);
const props = withDefaults(defineProps<PopupProps>(), {
  canDismiss: true,
  text: "",
  title: "",
  subtitle: "",
  onClose: () => {},
  leftButton: () => ({}),
  rightButton: () => ({}),
  showRightButton: true,
  customNode: null,
  scrollPickerOptions: () => [],
  scrollPickerSelections: () => [],
  radioPickerOptions: () => [],
});

const state = reactive({
  selections: props.scrollPickerSelections,
  inputValue: props.inputOptions?.value,
});

const $overlay = ref<HTMLElement>();
const visible = ref(false);
const inputError = ref({ showErrorText: false, disabledDialogRightButton: false });

const close = () => {
  if (props.canDismiss) {
    visible.value = false;
  }
};

const handleClick = (onClick: (...result: any[]) => boolean, type?: number) => {
  let result = false;
  if (props.type === "dialog-scroll-picker") {
    result = onClick(state.selections);
  } else if (props.type === "dialog-input") {
    if (!type && (inputError.value?.showErrorText)) {
      emits("error");
      // return;
    }
    result = onClick(state.inputValue);
  } else {
    result = onClick();
  }
  if (result) {
    emits("close");
  }
};

const onClickLeftButton = () => {
  const onClick = props.leftButton.onClick || (() => true);
  handleClick(onClick, 1);
};

const onClickRightButton = () => {
  if (inputError.value?.disabledDialogRightButton) return;
  const onClick = props.rightButton.onClick || (() => true);
  handleClick(onClick);
};

const CustomNode = defineComponent({
  render() {
    return props.customNode;
  },
});
const onInputChange = (value) => {
  state.inputValue = value
};
const onInputError = (e) => {
  inputError.value = e;
};

defineExpose({
  visible,
  close,
});

onMounted(() => {
  visible.value = true;
});
</script>

<template>
  <Transition @before-leave="$emit('close')" @after-leave="$emit('destroy')">
    <div v-show="visible" ref="$overlay" class="hi-overlay" @click="close">
      <div class="hi-popup" :class="type" @click.stop="">
        <template v-if="type === 'loading'">
          <div class="popup-main">
            <p>{{ text }}</p>
            <div class="img"></div>
          </div>
        </template>
        <template v-else-if="type.includes('dialog')">
          <div
            v-if="title"
            class="header"
            :style="{
              height: title && subtitle ? 72 : 56
            }"
          >
            <p class="text-first">{{ title }}</p>
            <p class="text-third" style="margin-top: 2px;">{{ subtitle }}</p>
          </div>
          <div class="popup-main">
            <template v-if="type === 'dialog'">
              <div class="flex items-center justify-center px-[1.2rem]">
                <p class="text-[1.1rem]">{{ text }}</p>
              </div>
            </template>
            <template v-else-if="type === 'dialog-input'">
              <div class="px-[24px] mb-[20px]">
                <XJInput
                  :value="state.inputValue"
                  :showErrorText="inputOptions?.showErrorText"
                  :errorText="inputOptions?.errorText"
                  :type="inputOptions?.type"
                  :placeholderText="inputOptions?.placeholderText"
                  :regInputFunc="inputOptions?.regInputFunc"
                  @change="onInputChange"
                  @error="onInputError"
                />
              </div>
            </template>
            <template v-else-if="type === 'dialog-scroll-picker'">
              <ScrollPicker class="mt-[8px]" :options="scrollPickerOptions" v-model="state.selections" />
            </template>
            <template v-else-if="type === 'dialog-custom'">
              <CustomNode />
            </template>
          </div>
          <div class="footer">
            <div class="buttons">
              <div class="button" @click="onClickLeftButton">
                <span :style="{ color: leftButton?.color || 'var(--color-text-second)' }">{{ leftButton?.text || tm('dialog.cancel') }}</span>
              </div>
              <div class="separator" v-if="rightButton && showRightButton"></div>
              <div class="button" @click="onClickRightButton" v-if="rightButton && showRightButton">
                <span :style="{ color: rightButton?.color || 'var(--active-color)' }">{{ rightButton?.text || tm('dialog.confirm') }}</span>
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>
  </Transition>
</template>

<style lang="scss" scoped>
.hi-overlay {
  @apply fixed top-0 bottom-0 left-0 right-0 flex items-center justify-end z-[999999] px-[12px];
  background-color: var(--bg-color__overlay);
  .hi-popup {
    @apply mb-[16px] rounded-[24px] w-full;
    background-color: #fff;
    &.loading {
      @apply p-[24px];
      .popup-main {
        @apply min-h-[48px] flex items-center justify-between;
        .img {
          @apply w-[40px] h-[48px] ml-[16px] flex-shrink-0 flex-grow-0 bg-no-repeat bg-contain bg-center;
        }
      }
    }

    &[class*="dialog"] {
      .header {
        @apply px-[24px] flex flex-col justify-center py-[12px] font-medium text-center;
        font-size: 1.2rem;
      }
      .popup-main {
        @apply mt-[24px];
        white-space: pre-line;
      }
      .header + .popup-main {
        @apply mt-0;
      }
      .footer {
        @apply h-[56px] mt-[8px] px-[16px];
        .buttons {
          @apply h-[40px] flex items-center;
          font-size: 1.1rem;
          .button {
            @apply h-[40px] p-[8px] flex-1 flex items-center justify-center;
          }
          .separator {
            @apply w-[1px] h-[24px] mx-[4px] flex-grow-0 flex-shrink-0 scale-x-[0.25];
            background-color: var(--separator-color);
          }
        }
      }
    }
  }
}
</style>
