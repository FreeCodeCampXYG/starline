import {
  type App,
  type ComponentInternalInstance,
  type VNode,
  createVNode,
  render,
  shallowReactive,
} from "vue";
import HiCenterConfirmConstructor, {
  type CenterConfirmDialogProps,
} from "./CenterConfirmDialog.vue";

export interface CenterConfirmHandler {
  close: () => void;
}

interface CenterConfirmInstance {
  id: string;
  vnode: VNode;
  handler: CenterConfirmHandler;
  vm: ComponentInternalInstance;
}

export type CenterConfirmOptions = Omit<
  CenterConfirmDialogProps,
  "onUnmountContainer"
>;

let seed = 1;

const instances: CenterConfirmInstance[] = shallowReactive([]);

const closeInstance = (instance: CenterConfirmInstance) => {
  const idx = instances.indexOf(instance);
  if (idx === -1) return;

  instances.splice(idx, 1);
  instance.handler.close();
};

const createInstance = (options: CenterConfirmOptions) => {
  const id = `xj-center-confirm_${seed++}`;
  const container = document.createElement("div");
  let instance!: CenterConfirmInstance;

  const userOnClose = options.onClose;

  const vnode = createVNode(HiCenterConfirmConstructor, {
    ...options,
    onClose: () => {
      userOnClose?.();
      closeInstance(instance);
    },
    onUnmountContainer: () => {
      render(null, container);
    },
  } as Record<string, unknown>);

  render(vnode, container);

  const el = container.firstElementChild;
  if (el) document.body.appendChild(el);

  const vm = vnode.component!;
  const handler: CenterConfirmHandler = {
    close: () => {
      vm.exposed!.visible.value = false;
    },
  };

  instance = {
    id,
    vnode,
    vm,
    handler,
  };

  return instance;
};

const centerConfirmDialog = (
  options: CenterConfirmOptions
): CenterConfirmHandler => {
  const instance = createInstance(options);
  instances.push(instance);
  return instance.handler;
};

centerConfirmDialog.install = (app: App) => {
  app.config.globalProperties.$centerConfirmDialog = centerConfirmDialog;
};

export default centerConfirmDialog;
