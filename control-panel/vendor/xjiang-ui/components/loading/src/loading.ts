import {
  type App,
  type ComponentInternalInstance,
  type VNode,
  createVNode,
  render,
  shallowReactive,
} from "vue";
import HiPopupConstructor, { type PopupProps } from "./Loading.vue";

export interface PopupHanlder {
  close: () => void;
}

export interface PopupInstance {
  id: string;
  vnode: VNode;
  handler: PopupHanlder;
  vm: ComponentInternalInstance;
  props: PopupProps;
}

export type PopupOptions = Omit<PopupProps, "id">;

let seed = 1;

const instances: PopupInstance[] = shallowReactive([]);

const closePopup = (instance: PopupInstance) => {
  const idx = instances.indexOf(instance);
  if (idx === -1) {
    return;
  }

  instances.splice(idx, 1);
  const { handler } = instance;
  handler.close();
};

const createPopup = (options: PopupOptions) => {
  const id = `xj-loading_${seed++}`;
  const container = document.createElement("div");
  const userOnClose = options.onClose;
  const props = {
    ...options,
    id,
    onClose: () => {
      userOnClose?.();
      closePopup(instance);
    },
    onDestroy: () => {
      render(null, container);
    },
  };

  const vnode = createVNode(HiPopupConstructor, props);
  render(vnode, container);

  document.body.appendChild(container.firstElementChild!);

  const vm = vnode.component!;
  const handler = {
    close: () => {
      vm.exposed!.visible.value = false;
    },
  };

  const instance: PopupInstance = {
    id,
    vnode,
    vm,
    handler,
    props: vm.props as unknown as PopupProps,
  };

  return instance;
};

const popup = (options: PopupOptions) => {
  const instance = createPopup(options);

  instances.push(instance);
  return instance.handler;
};

popup.install = (app: App) => {
  app.config.globalProperties.$popup = popup;
};

export default popup;
