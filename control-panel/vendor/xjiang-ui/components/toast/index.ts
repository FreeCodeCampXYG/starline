export {};
import {
  App,
  ComponentInternalInstance,
  VNode,
  createVNode,
  render,
  shallowReactive,
} from "vue";
import ToastConstructor, { ToastProps } from "./Toast.vue";

export interface ToastHanlder {
  close: () => void;
}

export interface ToastInstance {
  id: string;
  vnode: VNode;
  handler: ToastHanlder;
  vm: ComponentInternalInstance;
  props: ToastProps;
}

export type ToastOptions = Omit<ToastProps, "id">;

let seed = 1;

const instances: ToastInstance[] = shallowReactive([]);

const closeToast = (instance: ToastInstance) => {
  const idx = instances.indexOf(instance);
  if (idx === -1) {
    return;
  }

  instances.splice(idx, 1);
  const { handler } = instance;
  handler.close();
};

const createToast = (options: ToastOptions) => {
  const id = `hi-toast_${seed++}`;
  const container = document.createElement("div");
  const userOnClose = options.onClose;
  const props = {
    ...options,
    id,
    onClose: () => {
      userOnClose?.();
      closeToast(instance);
    },
    onDestroy: () => {
      render(null, container);
    },
  };

  const vnode = createVNode(ToastConstructor, props);
  render(vnode, container);

  document.body.appendChild(container.firstElementChild!);

  const vm = vnode.component!;
  const handler = {
    close: () => {
      vm.exposed!.visible.value = false;
    },
  };

  const instance: ToastInstance = {
    id,
    vnode,
    vm,
    handler,
    props: vm.props as unknown as ToastProps,
  };

  return instance;
};

const toast = (options: ToastOptions) => {
  const instance = createToast(options);

  instances.push(instance);
  return instance.handler;
};

toast.install = (app: App) => {
  app.config.globalProperties.$toast = toast;
};

export default toast;
