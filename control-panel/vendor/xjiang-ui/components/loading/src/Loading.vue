<!-- eslint-disable vue/multi-word-component-names -->
<script setup lang="ts">
import { type VNode, onMounted, ref, defineComponent, reactive } from "vue";
import i18n from "../../../i18n";
import Icon from "../../icon/index.vue";

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
  type: "loading" | "dialog";
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
});

const $overlay = ref<HTMLElement>();
const visible = ref(false);

const close = () => {
  if (props.canDismiss) {
    visible.value = false;
  }
};

const handleClick = (onClick: (...result: any[]) => boolean) => {
  let result = false;
  result = onClick();
  if (result) {
    emits("close");
  }
};

const onClickLeftButton = () => {
  const onClick = props.leftButton.onClick || (() => true);
  handleClick(onClick);
};

const onClickRightButton = () => {
  const onClick = props.rightButton.onClick || (() => true);
  handleClick(onClick);
};

const CustomNode = defineComponent({
  render() {
    return props.customNode;
  },
});

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
        <div class="popup-main">
          <div class="loading-icon">
            <Icon name="icon-connect" width="2.6rem" height="2.6rem" />
          </div>
          <p class="text-center">{{ text }}</p>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style lang="scss" scoped>
@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.hi-overlay {
  @apply fixed top-0 bottom-0 left-0 right-0 flex items-center justify-center z-[999999] px-[12px];
  background-color: var(--bg-color__overlay);
  .hi-popup {
    @apply rounded-[12px];
    background-color: rgba(0,0,0,.6); color: #ffffff;
    &.loading {
      @apply mt-[-2rem] py-[24px] px-[12px] text-[1.15rem];
      .popup-main {
        @apply min-h-[48px] flex flex-col items-center justify-between min-w-[100px] text-center;
        p {
          @apply w-full mt-[10px];
        }
        .img {
          @apply w-[40px] h-[48px] ml-[16px] flex-shrink-0 flex-grow-0 bg-no-repeat bg-contain bg-center;
        }
        .loading-icon {
          animation: spin 2.4s linear infinite;
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
