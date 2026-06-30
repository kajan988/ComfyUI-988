import { app } from "/scripts/app.js";
import { api } from "/scripts/api.js";
import { ComfyDialog, $el } from "/scripts/ui.js";
import { ComfyApp } from "/scripts/app.js";

function imageToBase64(url, callback) {
  fetch(url)
    .then((response) => response.blob())
    .then((blob) => {
      const reader = new FileReader();
      reader.readAsDataURL(blob);
      reader.onloadend = () => {
        const base64String = reader.result;
        callback(base64String);
      };
    });
}

async function uploadFile(formData) {
  const resp = await api.fetchApi('/upload/image', {
    method: 'POST',
    body: formData
  })
  if (resp.status === 200) {
    const data = await resp.json();
    const idx = ComfyApp.clipspace['selectedIndex'];
    const imgUrl = `view?filename=${data.name}&subfolder=${data.subfolder}&type=${data.type}`;
    const img = await new Promise(resolve => {
      const i = new Image();
      i.onload = () => resolve(i);
      i.onerror = () => resolve(i);
      i.src = imgUrl;
    });
    ComfyApp.clipspace.imgs[idx] = img;
    if (ComfyApp.clipspace.images) {
      ComfyApp.clipspace.images[idx] = {
        filename: data.name,
        subfolder: data.subfolder,
        type: data.type
      };
    }
    return data;
  } else {
    alert(resp.status + " - " + resp.statusText);
  }
}

class PhotopeaEditorDialog extends ComfyDialog {
  static instance = null;

  static getInstance() {
    if(!PhotopeaEditorDialog.instance) {
      PhotopeaEditorDialog.instance = new PhotopeaEditorDialog();
    }
    return PhotopeaEditorDialog.instance;
  }

  constructor() {
    super();
    this.element = $el("div.comfy-modal", { parent: document.body },
      [ $el("div.comfy-modal-content",
        [...this.createButtons()]),
      ]);
    this.iframe = null;
    this.iframe_container = null;
  }

  createButtons() {
    return [];
  }

  createButton(name, callback) {
    var button = document.createElement("button");
    button.innerText = name;
    button.addEventListener("click", callback);
    return button;
  }

  createLeftButton(name, callback) {
    var button = this.createButton(name, callback);
    button.style.cssFloat = "left";
    button.style.marginRight = "4px";
    return button;
  }

  createRightButton(name, callback) {
    var button = this.createButton(name, callback);
    button.style.cssFloat = "right";
    button.style.marginLeft = "4px";
    return button;
  }

  setlayout() {
    const self = this;

    var bottom_panel = document.createElement("div");
    bottom_panel.style.position = "absolute";
    bottom_panel.style.bottom = "0px";
    bottom_panel.style.left = "20px";
    bottom_panel.style.right = "20px";
    bottom_panel.style.height = "50px";
    this.element.appendChild(bottom_panel);

    self.fullscreenButton = this.createLeftButton("Fullscreen", () => {
      self.toggleFullscreen();
    });

    var cancelButton = this.createRightButton("Cancel", () => {
        self.close();
      });

    self.saveButton = this.createRightButton("Save", () => {
        self.save(self);
    });

    bottom_panel.appendChild(self.fullscreenButton);
    bottom_panel.appendChild(self.saveButton);
    bottom_panel.appendChild(cancelButton);
  }

  show() {
    if(!this.is_layout_created) {
      this.setlayout();
      this.is_layout_created = true;
    }

    if(ComfyApp.clipspace_return_node) {
      this.saveButton.innerText = "Save to node";
    }
    else {
      this.saveButton.innerText = "Save";
    }

    this.iframe = $el("iframe", {
      src: `https://www.photopea.com/`,
      style: {
        width: "100%",
        height: "100%",
        border: "none",
        position: "relative",
      },
    });

    this.iframe_container = document.createElement("div");
    this.iframe_container.style.flex = "1";
    this.iframe_container.style.paddingBottom = "70px";
    this.element.appendChild(this.iframe_container);
    this.element.style.display = "flex";
    this.element.style.flexDirection = "column";
    this.element.style.width = "80vw";
    this.element.style.height = "80vh";
    this.element.style.maxWidth = "100vw";
    this.element.style.maxHeight = "100vh";
    this.element.style.padding = "0";
    this.element.style.zIndex = 8888;
    this.iframe_container.appendChild(this.iframe);

    this.iframe.onload = () => {
      const target_image_path = ComfyApp.clipspace.imgs[ComfyApp.clipspace['selectedIndex']].src;
      imageToBase64(target_image_path, (dataURL) => {
        this.postMessageToPhotopea(`app.open("${dataURL}", null, false);`, "*");
      });
    };
  }

  close() {
    this.element.removeChild(this.iframe_container);
    super.close();
  }

  async save(self) {
    const saveMessage = 'app.activeDocument.saveToOE("png");';
    const [payload, done] = await self.postMessageToPhotopea(saveMessage);
    const file = new Blob([payload], { type: "image/png" });
    const body = new FormData();

    const filename = "clipspace-photopea-" + performance.now() + ".png";

    if(ComfyApp.clipspace.widgets) {
      const index = ComfyApp.clipspace.widgets.findIndex(obj => obj.name === 'image');
      if(index >= 0)
        ComfyApp.clipspace.widgets[index].value = filename;
    }

    body.append("image", file, filename);
    const data = await uploadFile(body);
    if (!data) return;

    ComfyApp.onClipspaceEditorSave();

    this.close();

    const returnNode = ComfyApp.clipspace_return_node;
    if (returnNode) {
      returnNode.imgs = [ComfyApp.clipspace.imgs[ComfyApp.clipspace.selectedIndex]];
      returnNode.imageIndex = 0;
      if (returnNode.graph) {
        returnNode.graph.setDirtyCanvas(true, true);
      }
    }
  }

  toggleFullscreen() {
    if (this.element.style.width === "100vw") {
      this.element.style.width = "80vw";
      this.element.style.height = "80vh";
      this.fullscreenButton.innerText = "Fullscreen";
    } else {
      this.element.style.width = "100vw";
      this.element.style.height = "100vh";
      this.fullscreenButton.innerText = "Exit Fullscreen";
    }
  }

  async postMessageToPhotopea(message) {
    var request = new Promise(function (resolve, reject) {
        var responses = [];
        var photopeaMessageHandle = function (response) {
            responses.push(response.data);
            if (response.data == "done") {
                window.removeEventListener("message", photopeaMessageHandle);
                resolve(responses)
            }
        };
        window.addEventListener("message", photopeaMessageHandle);
    });
    this.iframe.contentWindow.postMessage(message, "*");
    return await request;
  }
}

app.registerExtension({
  name: "988.Photopea",

  async setup(app) {
    const origOpenClipspace = app.openClipspace;
    if (origOpenClipspace) {
      app.openClipspace = function () {
        origOpenClipspace.apply(this, arguments);
        setTimeout(() => {
          const dialog = document.querySelector(".comfy-modal");
          if (!dialog) return;
          const content = dialog.querySelector(".comfy-modal-content");
          if (!content || content.querySelector("[data-photopea-btn]")) return;
          const btn = document.createElement("button");
          btn.setAttribute("data-photopea-btn", "");
          btn.type = "button";
          btn.textContent = "Photopea Editor";
          btn.onclick = () => {
            PhotopeaEditorDialog.getInstance().show();
          };
          const buttons = content.querySelectorAll("button");
          const closeBtn = buttons[buttons.length - 1];
          if (closeBtn) {
            content.insertBefore(btn, closeBtn);
          } else {
            content.appendChild(btn);
          }
        }, 10);
      };
    }

    function findMaskEditorButton(toolbox) {
      const candidates = toolbox.querySelectorAll('button');
      for (const btn of candidates) {
        const text = (btn.title || btn.textContent || btn.getAttribute('aria-label') || '').toLowerCase();
        if (text.includes('mask') || text.includes('edit or mask')) {
          return btn;
        }
      }
      return null;
    }

    function addPhotopeaButton(toolbox) {
      if (!toolbox || toolbox.querySelector('[data-photopea-toolbox-btn]')) return;

      const maskEditorBtn = findMaskEditorButton(toolbox);
      if (!maskEditorBtn) return;

      const btn = document.createElement("button");
      btn.setAttribute("data-photopea-toolbox-btn", "");
      btn.type = "button";
      btn.title = "Open in Photopea Editor";

      const iconSvg = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/><path d="m15 5 4 4"/></svg>';

      btn.className = maskEditorBtn.className;
      btn.innerHTML = iconSvg;
      btn.onclick = () => {
        const node = app.canvas.selected_nodes?.[Object.keys(app.canvas.selected_nodes)[0]];
        if (!node) return;
        if (!node.imgs?.length && node.previewMediaType !== "image") return;
        ComfyApp.copyToClipspace(node);
        ComfyApp.clipspace_return_node = node;
        PhotopeaEditorDialog.getInstance().show();
      };

      maskEditorBtn.parentNode.insertBefore(btn, maskEditorBtn.nextSibling);
    }

    const toolboxObserver = new MutationObserver(() => {
      const toolbox = document.querySelector('[data-testid="selection-toolbox"]');
      if (!toolbox) return;

      const photopeaBtn = toolbox.querySelector('[data-photopea-toolbox-btn]');
      const maskEditorBtn = findMaskEditorButton(toolbox);

      if (maskEditorBtn && !photopeaBtn) {
        addPhotopeaButton(toolbox);
      } else if (!maskEditorBtn && photopeaBtn) {
        photopeaBtn.remove();
      }
    });

    toolboxObserver.observe(document.body, { childList: true, subtree: true });
  },

  async beforeRegisterNodeDef(nodeType, nodeData, app) {
    if (Array.isArray(nodeData.output) && (nodeData.output.includes("MASK") || nodeData.output.includes("IMAGE"))) {
      const getOpts = nodeType.prototype.getExtraMenuOptions;
      nodeType.prototype.getExtraMenuOptions = function () {
        const r = getOpts ? getOpts.apply(this, arguments) : undefined;
        const opts = arguments[1];

        if (Array.isArray(opts)) {
          const maskEditorIdx = opts.findIndex(
            (opt) => opt && opt.content && typeof opt.content === "string" && opt.content.includes("Open in Mask Editor")
          );

          if (maskEditorIdx >= 0) {
            const hasImages = this.imgs?.length > 0 || this.previewMediaType === "image";

            opts.splice(maskEditorIdx + 1, 0, {
              content: "Open in Photopea Editor",
              disabled: !hasImages,
              callback: () => {
                ComfyApp.copyToClipspace(this);
                ComfyApp.clipspace_return_node = this;
                PhotopeaEditorDialog.getInstance().show();
              },
            });
          }
        }

        return r;
      };
    }
  }
});
