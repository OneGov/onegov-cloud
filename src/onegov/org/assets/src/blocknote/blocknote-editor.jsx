import {
  BlockNoteEditor,
  BlockNoteSchema,
  createHeadingBlockSpec,
  createStyleSpec,
  defaultBlockSpecs,
  defaultInlineContentSpecs,
  defaultStyleSpecs,
} from '@blocknote/core';
import {de, en, fr, it} from '@blocknote/core/locales';
import {filterSuggestionItems, insertOrUpdateBlockForSlashMenu} from '@blocknote/core/extensions';
import {BlockNoteView} from '@blocknote/mantine';
import {
  BasicTextStyleButton,
  BlockTypeSelect,
  CreateLinkButton,
  DragHandleMenu,
  FileCaptionButton,
  FormattingToolbar,
  FormattingToolbarController,
  getDefaultReactSlashMenuItems,
  NestBlockButton,
  RemoveBlockItem,
  SideMenu,
  SideMenuController,
  SuggestionMenuController,
  TableColumnHeaderItem,
  TableRowHeaderItem,
  UnnestBlockButton,
  createReactBlockSpec,
  useBlockNoteEditor,
  useComponentsContext,
  useCreateBlockNote,
  useEditorState,
} from '@blocknote/react';
import {
  AIExtension,
  AIMenuController,
  AIToolbarButton,
  aiDocumentFormats,
  getAISlashMenuItems,
} from '@blocknote/xl-ai';
import {
  de as aiDe,
  en as aiEn,
  fr as aiFr,
  it as aiIt,
} from '@blocknote/xl-ai/locales';
import {DefaultChatTransport} from 'ai';
import React, {useCallback, useEffect, useMemo, useRef, useState} from 'react';
import {createRoot} from 'react-dom/client';
import Cropper from 'react-easy-crop';

import '@blocknote/mantine/style.css';
import '@blocknote/xl-ai/style.css';
import 'react-easy-crop/react-easy-crop.css';
import './blocknote-editor.css';


const dictionaries = {de, en, fr, it};
const aiDictionaries = {de: aiDe, en: aiEn, fr: aiFr, it: aiIt};
const mountedEditors = new WeakMap();
const registeredForms = new WeakMap();
const alphaListMarker = 'onegov-alpha-list';


const hasAddressableAIBlocks = documentState => {
  const blocks = documentState.selection
    ? documentState.selectedBlocks
    : documentState.blocks;
  return Array.isArray(blocks) && blocks.some(block => (
    typeof block?.id === 'string' && block.id.length > 0
  ));
};


const buildAddressableAIDocumentState = async aiRequest => {
  const builder = aiDocumentFormats.html.defaultDocumentStateBuilder;
  const documentState = await builder(aiRequest);
  if (hasAddressableAIBlocks(documentState)) {
    return documentState;
  }

  // BlockNote can produce an empty selectedBlocks array after its selection
  // has been hidden for the AI menu. Rebuild the request without that empty
  // selection so the backend always receives real editor block IDs.
  return builder({...aiRequest, selectedBlocks: undefined});
};


const isAlphaListBlock = block => (
  block.type === 'numberedListItem' &&
  block.props.backgroundColor === alphaListMarker
);


const isEmptyParagraphBlock = block => (
  block.type === 'paragraph' &&
  (!block.content || block.content.length === 0) &&
  (!block.children || block.children.length === 0)
);


const alphaListLabel = position => {
  let label = '';
  let remainder = position;

  while (remainder > 0) {
    remainder -= 1;
    label = String.fromCharCode(97 + (remainder % 26)) + label;
    remainder = Math.floor(remainder / 26);
  }
  return `${label}.`;
};


const translate = text => window.locale ? window.locale(text) : text;


const language = () => {
  const value = window.locale?.language || document.documentElement.lang || 'de';
  const code = String(value).toLowerCase().split(/[-_]/)[0];

  return dictionaries[code] ? code : 'en';
};


const makeBooleanStyle = (type, tagName, aliases = []) => createStyleSpec(
  {type, propSchema: 'boolean'},
  {
    render: () => {
      const dom = document.createElement(tagName);
      return {dom, contentDOM: dom};
    },
    toExternalHTML: () => {
      const dom = document.createElement(tagName);
      return {dom, contentDOM: dom};
    },
    parse: element => (
      [tagName, ...aliases].includes(element.tagName.toLowerCase())
        ? true
        : undefined
    ),
  },
);


const deletedStyle = makeBooleanStyle('strike', 'del', ['s']);
const superscriptStyle = makeBooleanStyle('superscript', 'sup');
const subscriptStyle = makeBooleanStyle('subscript', 'sub');


const editNoteBlock = createReactBlockSpec(
  {
    type: 'editNote',
    propSchema: {},
    content: 'inline',
  },
  {
    parse: element => (
      element.hasAttribute('data-onegov-edit-note') || (
        element.tagName === 'P' && element.classList.contains('edit-note')
      )
        ? {}
        : undefined
    ),
    render: ({contentRef}) => (
      <p className="edit-note onegov-blocknote-edit-note" ref={contentRef} />
    ),
    toExternalHTML: ({contentRef}) => (
      <p className="edit-note" ref={contentRef} />
    ),
  },
)();


const photoAlbumBlock = createReactBlockSpec(
  {
    type: 'photoAlbum',
    propSchema: {
      url: {default: ''},
      title: {default: ''},
    },
    content: 'none',
  },
  {
    parse: element => {
      if (!element.hasAttribute('data-onegov-photo-album')) {
        return undefined;
      }
      const link = element.querySelector('a[href]');
      if (!link) {
        return undefined;
      }
      return {
        url: link.getAttribute('href') || '',
        title: link.textContent.trim(),
      };
    },
    render: ({block}) => {
      const title = block.props.title || block.props.url;
      return (
        <div
          aria-label={`${translate('Photo Album')}: ${title}`}
          className="onegov-blocknote-photo-album"
          contentEditable={false}
          draggable={false}
          role="group"
        >
          <span aria-hidden="true" className="onegov-blocknote-photo-album-icon">
            ▦
          </span>
          <span className="onegov-blocknote-photo-album-content">
            <strong>{title}</strong>
            <span>{block.props.url}</span>
          </span>
        </div>
      );
    },
    toExternalHTML: ({block}) => (
      <p className="onegov-photoalbum-block">
        <a href={block.props.url}>
          {block.props.title || block.props.url}
        </a>
      </p>
    ),
  },
)();


const schema = BlockNoteSchema.create({
  blockSpecs: {
    paragraph: defaultBlockSpecs.paragraph,
    heading: createHeadingBlockSpec({
      defaultLevel: 2,
      levels: [2, 3, 4, 5],
      allowToggleHeadings: true,
    }),
    bulletListItem: defaultBlockSpecs.bulletListItem,
    numberedListItem: defaultBlockSpecs.numberedListItem,
    codeBlock: defaultBlockSpecs.codeBlock,
    divider: defaultBlockSpecs.divider,
    file: defaultBlockSpecs.file,
    image: defaultBlockSpecs.image,
    quote: defaultBlockSpecs.quote,
    table: defaultBlockSpecs.table,
    editNote: editNoteBlock,
    photoAlbum: photoAlbumBlock,
  },
  inlineContentSpecs: defaultInlineContentSpecs,
  styleSpecs: {
    bold: defaultStyleSpecs.bold,
    italic: defaultStyleSpecs.italic,
    strike: deletedStyle,
    code: defaultStyleSpecs.code,
    superscript: superscriptStyle,
    subscript: subscriptStyle,
  },
});


const withoutIds = value => {
  if (Array.isArray(value)) {
    return value.map(withoutIds);
  }
  if (value && typeof value === 'object') {
    return Object.fromEntries(Object.entries(value)
      .filter(([key]) => key !== 'id')
      .map(([key, child]) => [key, withoutIds(child)]));
  }
  return value;
};


const signature = value => JSON.stringify(withoutIds(value));


const prepareHtmlForImport = html => {
  const template = document.createElement('template');
  template.innerHTML = html;

  template.content.querySelectorAll('p.edit-note').forEach(note => {
    const replacement = document.createElement('div');
    replacement.dataset.onegovEditNote = '';
    replacement.append(...Array.from(note.childNodes));
    note.replaceWith(replacement);
  });

  template.content.querySelectorAll('p.onegov-file-block').forEach(file => {
    const link = file.querySelector('a[href]');
    if (!link) {
      return;
    }
    const replacement = document.createElement('embed');
    replacement.setAttribute('src', link.getAttribute('href'));
    file.replaceWith(replacement);
  });

  template.content.querySelectorAll('p.onegov-photoalbum-block')
    .forEach(album => {
      const link = album.querySelector('a[href]');
      if (!link) {
        return;
      }
      const replacement = document.createElement('div');
      replacement.dataset.onegovPhotoAlbum = '';
      replacement.append(link.cloneNode(true));
      album.replaceWith(replacement);
    });

  return template.innerHTML;
};


let htmlParser;


const getHtmlParser = () => {
  if (!htmlParser) {
    htmlParser = BlockNoteEditor.create({
      schema,
      dictionary: dictionaries[language()],
    });
  }
  return htmlParser;
};


const parseInitialHtml = html => {
  const parser = getHtmlParser();
  const template = document.createElement('template');
  const blocks = [];
  const groups = [];

  template.innerHTML = html || '';

  Array.from(template.content.childNodes).forEach(node => {
    const fragment = node.nodeType === Node.ELEMENT_NODE
      ? node.outerHTML
      : node.textContent;
    let importFragment = prepareHtmlForImport(fragment);

    if (!fragment || !fragment.trim()) {
      return;
    }

    if (
      node.nodeType === Node.ELEMENT_NODE &&
      node.tagName === 'PRE' &&
      (
        node.childElementCount !== 1 ||
        node.firstElementChild?.tagName !== 'CODE'
      )
    ) {
      const pre = document.createElement('pre');
      const code = document.createElement('code');
      code.textContent = node.textContent;
      pre.append(code);
      importFragment = pre.outerHTML;
    }

    const parsed = parser.tryParseHTMLToBlocks(importFragment);
    if (!parsed.length) {
      return;
    }

    if (
      node.nodeType === Node.ELEMENT_NODE &&
      node.matches('p.onegov-file-block')
    ) {
      const link = node.querySelector('a[href]');
      const file = parsed.find(block => block.type === 'file');
      if (link && file) {
        file.props.url = link.getAttribute('href');
        file.props.name = link.textContent.trim() || file.props.url;
      }
    }

    if (
      node.nodeType === Node.ELEMENT_NODE &&
      node.tagName === 'OL' &&
      node.classList.contains('alpha-list')
    ) {
      let alphaIndex = 0;
      parsed.forEach(block => {
        if (block.type === 'numberedListItem') {
          alphaIndex += 1;
          block.props.backgroundColor = alphaListMarker;
          block.props.textColor = alphaListLabel(alphaIndex);
        }
      });
    }

    groups.push({
      html: fragment,
      ids: parsed.map(block => block.id),
      signatures: Object.fromEntries(
        parsed.map(block => [block.id, signature(block)]),
      ),
    });
    blocks.push(...parsed);
  });

  if (!blocks.length) {
    blocks.push({type: 'paragraph'});
  }

  return {blocks, groups, originalHtml: html || ''};
};


const serializeEditor = state => {
  const blocks = state.editor.document;
  const completeSignature = signature(blocks);

  if (
    state.sourceOverride &&
    state.sourceOverride.signature === completeSignature
  ) {
    return state.sourceOverride.html;
  }
  state.sourceOverride = null;

  if (blocks.length === 1 && isEmptyParagraphBlock(blocks[0])) {
    const group = state.initial.groups.length === 1
      ? state.initial.groups[0]
      : undefined;
    const unchangedInitialEmptyBlock = group?.ids.length === 1 &&
      group.ids[0] === blocks[0].id &&
      group.signatures[blocks[0].id] === signature(blocks[0]);

    if (!unchangedInitialEmptyBlock) {
      return '';
    }
  }

  const currentById = new Map(blocks.map(block => [block.id, block]));
  const groupById = new Map();
  state.initial.groups.forEach(group => {
    group.ids.forEach(id => groupById.set(id, group));
  });

  const emittedGroups = new Set();
  const output = [];

  const serializeBlocks = selectedBlocks => {
    const template = document.createElement('template');
    const prepareExternalBlock = block => ({
      ...block,
      children: block.children?.map(prepareExternalBlock),
      props: isAlphaListBlock(block)
        ? {...block.props, textColor: 'default'}
        : block.props,
    });
    const externalBlocks = selectedBlocks.map(prepareExternalBlock);
    template.innerHTML = state.editor.blocksToHTMLLossy(externalBlocks);

    if (selectedBlocks.length === 1 && selectedBlocks[0].type === 'file') {
      const {name, url} = selectedBlocks[0].props;
      const paragraph = document.createElement('p');
      const link = document.createElement('a');
      paragraph.className = 'onegov-file-block';
      link.setAttribute('href', url);
      link.textContent = name || url;
      paragraph.append(link);
      template.innerHTML = '';
      template.content.append(paragraph);
    }

    if (
      selectedBlocks.length &&
      selectedBlocks.every(block => (
        isAlphaListBlock(block)
      ))
    ) {
      template.content.firstElementChild?.classList.add('alpha-list');
    }

    template.content.querySelectorAll(
      `[data-background-color="${alphaListMarker}"]`,
    ).forEach(element => {
      element.removeAttribute('data-background-color');
      element.style.removeProperty('background-color');
      if (!element.getAttribute('style')) {
        element.removeAttribute('style');
      }
    });

    return Array.from(template.content.childNodes).map(node => (
      node.nodeType === Node.ELEMENT_NODE ? node.outerHTML : node.textContent
    )).join('');
  };

  for (let index = 0; index < blocks.length; index += 1) {
    const block = blocks[index];
    const group = groupById.get(block.id);

    if (
      block.type === 'bulletListItem' ||
      block.type === 'numberedListItem'
    ) {
      const isAlpha = block.props.backgroundColor === alphaListMarker;
      const listBlocks = [];
      let cursor = index;
      while (
        cursor < blocks.length &&
        blocks[cursor].type === block.type &&
        (
          blocks[cursor].props.backgroundColor === alphaListMarker
        ) === isAlpha
      ) {
        listBlocks.push(blocks[cursor]);
        cursor += 1;
      }

      const unchangedGroup = group &&
        !emittedGroups.has(group) &&
        listBlocks.length === group.ids.length &&
        listBlocks.every((item, offset) => (
          item.id === group.ids[offset] &&
          signature(item) === group.signatures[item.id]
        ));
      if (unchangedGroup) {
        output.push(group.html);
      } else {
        output.push(serializeBlocks(listBlocks));
      }
      listBlocks.forEach(item => {
        const itemGroup = groupById.get(item.id);
        if (itemGroup) {
          emittedGroups.add(itemGroup);
        }
      });
      index = cursor - 1;
      continue;
    }

    if (!group || emittedGroups.has(group)) {
      output.push(serializeBlocks([block]));
      continue;
    }

    const groupBlocks = group.ids
      .map(id => currentById.get(id))
      .filter(Boolean);
    const presentIds = groupBlocks.map(item => item.id);
    const contiguousIds = blocks
      .slice(index, index + presentIds.length)
      .map(item => item.id);
    const unchanged = presentIds.length === group.ids.length &&
      JSON.stringify(presentIds) === JSON.stringify(group.ids) &&
      JSON.stringify(contiguousIds) === JSON.stringify(group.ids) &&
      groupBlocks.every(item => (
        signature(item) === group.signatures[item.id]
      ));

    emittedGroups.add(group);
    if (unchanged) {
      output.push(group.html);
      index += groupBlocks.length - 1;
    } else {
      output.push(serializeBlocks([block]));
    }
  }

  return output.join('');
};


const writeTextarea = state => {
  if (!state.editor) {
    return;
  }
  state.textarea.value = serializeEditor(state);
  state.textarea.dispatchEvent(new Event('input', {bubbles: true}));
};


const syncTextarea = state => {
  state.syncRevision += 1;
  writeTextarea(state);
};


const scheduleTextareaSync = state => {
  const revision = state.syncRevision + 1;
  state.syncRevision = revision;

  // BlockNote's HTML exporter renders React block views internally. Running
  // it inside ProseMirror's update callback can leave React work pending until
  // the next selection change. Finish the editor transaction first, then
  // serialize the latest document. A synchronous form submit invalidates this
  // queued revision and flushes the current document itself.
  requestAnimationFrame(() => {
    if (revision === state.syncRevision) {
      writeTextarea(state);
    }
  });
};


const normalizeAlphaListLabels = state => {
  if (!state.editor || state.normalizingAlphaLists) {
    return;
  }

  const updates = [];
  const collectUpdates = blocks => {
    let alphaIndex = 0;

    blocks.forEach(block => {
      if (isAlphaListBlock(block)) {
        alphaIndex += 1;
        const label = alphaListLabel(alphaIndex);
        if (block.props.textColor !== label) {
          updates.push({block, label});
        }
      } else {
        alphaIndex = 0;
      }

      if (block.children?.length) {
        collectUpdates(block.children);
      }
    });
  };

  collectUpdates(state.editor.document);
  if (!updates.length) {
    return;
  }

  state.normalizingAlphaLists = true;
  try {
    state.editor.transact(() => {
      updates.forEach(({block, label}) => state.editor.updateBlock(block, {
        props: {textColor: label},
      }));
    });
  } finally {
    state.normalizingAlphaLists = false;
  }
};


const handleEditorChange = state => {
  if (state.normalizingAlphaLists) {
    return;
  }
  normalizeAlphaListLabels(state);
  scheduleTextareaSync(state);
};


const reportError = error => {
  const message = error?.message || String(error);

  if (window.console) {
    window.console.error(error);
  }
  if (typeof window.handleUploadError === 'function') {
    window.handleUploadError({message});
  } else if (typeof window.show_confirmation === 'function') {
    window.show_confirmation(message, undefined, 'Ok');
  }
};


const imageOutput = file => {
  const supportedTypes = ['image/jpeg', 'image/png', 'image/webp'];
  const type = supportedTypes.includes(file.type) ? file.type : 'image/png';

  if (type === file.type) {
    return {name: file.name, type};
  }

  const basename = file.name.replace(/\.[^.]*$/, '') || 'image';
  return {name: `${basename}.png`, type};
};


const loadCropImage = source => new Promise((resolve, reject) => {
  const image = new Image();

  image.addEventListener('load', () => resolve(image), {once: true});
  image.addEventListener('error', reject, {once: true});
  image.src = source;
});


const renderCroppedImage = async (source, area, rotation, sourceFile) => {
  const image = await loadCropImage(source);
  const radians = rotation * Math.PI / 180;
  const boundingWidth = (
    Math.abs(Math.cos(radians) * image.naturalWidth) +
    Math.abs(Math.sin(radians) * image.naturalHeight)
  );
  const boundingHeight = (
    Math.abs(Math.sin(radians) * image.naturalWidth) +
    Math.abs(Math.cos(radians) * image.naturalHeight)
  );
  const rotated = document.createElement('canvas');
  const context = rotated.getContext('2d');

  if (!context) {
    throw new Error(translate('The image could not be cropped.'));
  }

  rotated.width = Math.ceil(boundingWidth);
  rotated.height = Math.ceil(boundingHeight);
  context.translate(rotated.width / 2, rotated.height / 2);
  context.rotate(radians);
  context.translate(-image.naturalWidth / 2, -image.naturalHeight / 2);
  context.drawImage(image, 0, 0);

  const cropped = document.createElement('canvas');
  const croppedContext = cropped.getContext('2d');
  const output = imageOutput(sourceFile);

  if (!croppedContext) {
    throw new Error(translate('The image could not be cropped.'));
  }

  cropped.width = Math.max(1, Math.round(area.width));
  cropped.height = Math.max(1, Math.round(area.height));
  if (output.type === 'image/jpeg') {
    croppedContext.fillStyle = '#fff';
    croppedContext.fillRect(0, 0, cropped.width, cropped.height);
  }
  croppedContext.drawImage(
    rotated,
    area.x,
    area.y,
    area.width,
    area.height,
    0,
    0,
    cropped.width,
    cropped.height,
  );

  const blob = await new Promise(resolve => cropped.toBlob(
    resolve,
    output.type,
    output.type === 'image/png' ? undefined : 0.92,
  ));
  if (!blob) {
    throw new Error(translate('The image could not be cropped.'));
  }

  return new File([blob], output.name, {
    lastModified: sourceFile.lastModified,
    type: output.type,
  });
};


const ImageCropDialog = ({file, imageUrl, onClose}) => {
  const [crop, setCrop] = useState({x: 0, y: 0});
  const [zoom, setZoom] = useState(1);
  const [rotation, setRotation] = useState(0);
  const [croppedArea, setCroppedArea] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState('');
  const cancelButton = useRef(null);

  useEffect(() => {
    cancelButton.current?.focus();
  }, [imageUrl]);

  const cancel = () => {
    if (!processing) {
      onClose(null);
    }
  };

  const apply = async () => {
    if (!croppedArea || processing) {
      return;
    }
    setProcessing(true);
    setError('');
    try {
      onClose(await renderCroppedImage(
        imageUrl,
        croppedArea,
        rotation,
        file,
      ));
    } catch (cropError) {
      setError(
        cropError?.message || translate('The image could not be cropped.'),
      );
      setProcessing(false);
    }
  };

  return (
    <div
      className="onegov-image-crop-overlay"
      onKeyDown={event => {
        event.stopPropagation();
        if (event.key === 'Escape') {
          event.preventDefault();
          cancel();
          return;
        }
        if (event.key === 'Tab') {
          const focusable = Array.from(event.currentTarget.querySelectorAll(
            'button:not([disabled]), input:not([disabled]), [tabindex="0"]',
          )).filter(element => element.getClientRects().length > 0);
          const first = focusable[0];
          const last = focusable[focusable.length - 1];

          if (event.shiftKey && document.activeElement === first) {
            event.preventDefault();
            last?.focus();
          } else if (!event.shiftKey && document.activeElement === last) {
            event.preventDefault();
            first?.focus();
          }
        }
      }}
      onMouseDown={event => {
        if (event.target === event.currentTarget) {
          cancel();
        }
      }}
    >
      <section
        aria-labelledby="onegov-image-crop-title"
        aria-modal="true"
        className="onegov-image-crop-dialog"
        role="dialog"
      >
        <h2 id="onegov-image-crop-title">{translate('Crop image')}</h2>
        <div className="onegov-image-crop-stage">
          <Cropper
            aspect={4 / 3}
            crop={crop}
            disableAutomaticStylesInjection={true}
            image={imageUrl}
            onCropChange={setCrop}
            onCropComplete={(_area, pixels) => setCroppedArea(pixels)}
            onRotationChange={setRotation}
            onZoomChange={setZoom}
            rotation={rotation}
            showGrid={true}
            zoom={zoom}
          />
        </div>
        <div className="onegov-image-crop-controls">
          <label>
            {translate('Zoom in/out')}
            <input
              max="3"
              min="1"
              name="image-crop-zoom"
              onChange={event => setZoom(Number(event.target.value))}
              step="0.1"
              type="range"
              value={zoom}
            />
          </label>
          <label>
            {translate('Rotation')}
            <input
              max="360"
              min="0"
              name="image-crop-rotation"
              onChange={event => setRotation(Number(event.target.value))}
              step="1"
              type="range"
              value={rotation}
            />
          </label>
        </div>
        {error && <p className="onegov-blocknote-error" role="alert">{error}</p>}
        <div className="onegov-image-crop-actions">
          <button
            className="button secondary"
            disabled={processing}
            onClick={cancel}
            ref={cancelButton}
            type="button"
          >
            {translate('Cancel')}
          </button>
          <button
            className="button"
            disabled={!croppedArea || processing}
            onClick={apply}
            type="button"
          >
            {processing ? `${translate('Upload')}…` : translate('Apply')}
          </button>
        </div>
      </section>
    </div>
  );
};


let imageCropRoot = null;
let imageCropOpen = false;


const readImageFile = file => new Promise((resolve, reject) => {
  const reader = new FileReader();

  reader.addEventListener('load', () => {
    if (typeof reader.result === 'string') {
      resolve(reader.result);
    } else {
      reject(new Error(translate('The image could not be cropped.')));
    }
  }, {once: true});
  reader.addEventListener('error', () => reject(
    reader.error || new Error(translate('The image could not be cropped.')),
  ), {once: true});
  reader.readAsDataURL(file);
});


const cropImageFile = async file => {
  if (!file?.type.startsWith('image/')) {
    return file;
  }
  if (imageCropOpen) {
    throw new Error(translate('An image is already being cropped.'));
  }
  imageCropOpen = true;

  let imageUrl;
  try {
    imageUrl = await readImageFile(file);
  } catch (error) {
    imageCropOpen = false;
    throw error;
  }

  if (!imageCropRoot) {
    const host = document.createElement('div');
    host.dataset.onegovImageCropRoot = '';
    document.body.append(host);
    imageCropRoot = createRoot(host);
  }

  return new Promise(resolve => {
    const finish = result => {
      imageCropRoot.render(null);
      imageCropOpen = false;
      resolve(result);
    };
    imageCropRoot.render(
      <ImageCropDialog file={file} imageUrl={imageUrl} onClose={finish} />,
    );
  });
};


const uploadFile = (state, file, blockId) => {
  const blockType = blockId ? state.editor?.getBlock(blockId)?.type : undefined;
  const endpoint = blockType === 'image' || (
    !blockType && file.type.startsWith('image/')
  )
    ? state.form?.dataset.imageUploadUrl
    : state.form?.dataset.fileUploadUrl;

  if (!endpoint) {
    return Promise.reject(new Error(translate('Upload is not available.')));
  }

  const body = new FormData();
  body.append('file', file);

  const request = fetch(endpoint, {
    method: 'POST',
    body,
    credentials: 'same-origin',
    headers: {'X-Requested-With': 'XMLHttpRequest'},
  }).then(async response => {
    let data;

    try {
      data = await response.json();
    } catch (_error) {
      throw new Error(translate('The upload failed.'));
    }

    if (!response.ok || data.error || !data.filelink) {
      throw new Error(data.message || translate('The upload failed.'));
    }

    return data.filelink;
  });

  state.pendingUploads.add(request);
  request.catch(reportError).finally(() => state.pendingUploads.delete(request));

  return request;
};


const registerForm = state => {
  const form = state.form;
  if (!form) {
    return;
  }

  let registration = registeredForms.get(form);
  if (!registration) {
    registration = {states: new Set(), resubmitting: false};
    registeredForms.set(form, registration);

    form.addEventListener('submit', event => {
      registration.states.forEach(syncTextarea);

      if (registration.resubmitting) {
        registration.resubmitting = false;
        return;
      }

      const pending = Array.from(registration.states)
        .flatMap(editorState => Array.from(editorState.pendingUploads));
      if (!pending.length) {
        return;
      }

      event.preventDefault();
      const submitter = event.submitter;
      Promise.allSettled(pending).then(results => {
        registration.states.forEach(syncTextarea);
        if (results.some(result => result.status === 'rejected')) {
          return;
        }
        registration.resubmitting = true;
        if (form.requestSubmit) {
          form.requestSubmit(submitter || undefined);
        } else {
          form.submit();
        }
      });
    });
  }
  registration.states.add(state);
};


const TextIcon = ({children}) => (
  <span aria-hidden="true" className="onegov-blocknote-icon">{children}</span>
);
const ParagraphIcon = props => <TextIcon {...props}>P</TextIcon>;
const H2Icon = props => <TextIcon {...props}>H2</TextIcon>;
const H3Icon = props => <TextIcon {...props}>H3</TextIcon>;
const H4Icon = props => <TextIcon {...props}>H4</TextIcon>;
const H5Icon = props => <TextIcon {...props}>H5</TextIcon>;
const ToggleH2Icon = props => <TextIcon {...props}>▸H2</TextIcon>;
const ToggleH3Icon = props => <TextIcon {...props}>▸H3</TextIcon>;
const QuoteIcon = props => <TextIcon {...props}>“</TextIcon>;
const BulletIcon = props => <TextIcon {...props}>•</TextIcon>;
const NumberIcon = props => <TextIcon {...props}>1.</TextIcon>;
const AlphaIcon = props => <TextIcon {...props}>a.</TextIcon>;
const EditNoteIcon = props => <TextIcon {...props}>!</TextIcon>;
const ImageIcon = props => <TextIcon {...props}>▧</TextIcon>;
const FileIcon = props => <TextIcon {...props}>⌕</TextIcon>;
const InternalLinkIcon = props => <TextIcon {...props}>↗</TextIcon>;
const PhotoAlbumIcon = props => <TextIcon {...props}>▦</TextIcon>;


const restoreEditorFocus = (editor, callback) => (...args) => {
  const result = callback(...args);
  window.requestAnimationFrame(() => editor.focus());
  return result;
};


const OneGovBlockTypeSelect = () => {
  const editor = useBlockNoteEditor(schema);
  const menu = editor.dictionary.slash_menu;
  const items = [
    {name: menu.paragraph.title, type: 'paragraph', icon: ParagraphIcon},
    {
      name: menu.heading_2.title,
      type: 'heading',
      props: {level: 2, isToggleable: false},
      icon: H2Icon,
    },
    {
      name: menu.heading_3.title,
      type: 'heading',
      props: {level: 3, isToggleable: false},
      icon: H3Icon,
    },
    {
      name: menu.heading_4.title,
      type: 'heading',
      props: {level: 4, isToggleable: false},
      icon: H4Icon,
    },
    {
      name: menu.heading_5.title,
      type: 'heading',
      props: {level: 5, isToggleable: false},
      icon: H5Icon,
    },
    {
      name: menu.toggle_heading_2.title,
      type: 'heading',
      props: {level: 2, isToggleable: true},
      icon: ToggleH2Icon,
    },
    {
      name: menu.toggle_heading_3.title,
      type: 'heading',
      props: {level: 3, isToggleable: true},
      icon: ToggleH3Icon,
    },
    {name: menu.quote.title, type: 'quote', icon: QuoteIcon},
    {name: menu.bullet_list.title, type: 'bulletListItem', icon: BulletIcon},
    {name: menu.numbered_list.title, type: 'numberedListItem', icon: NumberIcon},
    {
      name: translate('Alphabetical list'),
      type: 'numberedListItem',
      props: {backgroundColor: alphaListMarker, textColor: 'a.'},
      icon: AlphaIcon,
    },
    {name: translate('Edit note'), type: 'editNote', icon: EditNoteIcon},
  ];

  return <BlockTypeSelect items={items} />;
};


// Toggle headings are useful in the rendered page but collapsing them while
// editing makes their child blocks difficult to reach. Open them through
// BlockNote's own button handler so empty toggles retain their add-block
// button and persist the open state across node-view replacements. The
// collapse control itself is hidden in editor mode through CSS.
const expandEditorToggleHeadings = root => {
  root.querySelectorAll('.bn-toggle-wrapper').forEach(toggleWrapper => {
    const toggleButton = toggleWrapper.querySelector('.bn-toggle-button');

    if (!(toggleButton instanceof HTMLButtonElement)) {
      return;
    }
    if (toggleWrapper.dataset.showChildren !== 'true') {
      toggleButton.click();
    }
  });
};


const InlineStyleButton = ({style, oppositeStyle, label, children}) => {
  const editor = useBlockNoteEditor(schema);
  const Components = useComponentsContext();
  const selected = useEditorState({
    editor,
    selector: snapshot => Boolean(snapshot.editor.getActiveStyles()[style]),
  });

  if (!Components) {
    return null;
  }

  return (
    <Components.FormattingToolbar.Button
      label={label}
      mainTooltip={label}
      isSelected={selected}
      onClick={() => {
        editor.focus();
        editor.transact(() => {
          editor.removeStyles({[oppositeStyle]: true});
          editor.toggleStyles({[style]: true});
        });
      }}
    >
      {children}
    </Components.FormattingToolbar.Button>
  );
};


const OneGovFormattingToolbar = ({aiEnabled}) => {
  const editor = useBlockNoteEditor(schema);
  const hasSelectedImage = useEditorState({
    editor,
    selector: snapshot => (
      snapshot.editor.getSelection()?.blocks || [
        snapshot.editor.getTextCursorPosition().block,
      ]
    ).some(block => block.type === 'image'),
  });

  return (
    <FormattingToolbar>
      <OneGovBlockTypeSelect />
      <BasicTextStyleButton basicTextStyle="bold" />
      <BasicTextStyleButton basicTextStyle="italic" />
      <BasicTextStyleButton basicTextStyle="strike" />
      <BasicTextStyleButton basicTextStyle="code" />
      {!hasSelectedImage && (
        <InlineStyleButton
          label={translate('Superscript')}
          oppositeStyle="subscript"
          style="superscript"
        >
          x<sup>2</sup>
        </InlineStyleButton>
      )}
      {!hasSelectedImage && (
        <InlineStyleButton
          label={translate('Subscript')}
          oppositeStyle="superscript"
          style="subscript"
        >
          x<sub>2</sub>
        </InlineStyleButton>
      )}
      {aiEnabled && !hasSelectedImage && <AIToolbarButton />}
      <CreateLinkButton />
      <FileCaptionButton />
      <NestBlockButton />
      <UnnestBlockButton />
    </FormattingToolbar>
  );
};


const OneGovDragHandleMenu = () => {
  const editor = useBlockNoteEditor(schema);
  const menu = editor.dictionary.drag_handle;

  return (
    <DragHandleMenu>
      <RemoveBlockItem>{menu.delete_menuitem}</RemoveBlockItem>
      <TableRowHeaderItem>{menu.header_row_menuitem}</TableRowHeaderItem>
      <TableColumnHeaderItem>
        {menu.header_column_menuitem}
      </TableColumnHeaderItem>
    </DragHandleMenu>
  );
};


const OneGovSideMenu = () => (
  <SideMenu dragHandleMenu={OneGovDragHandleMenu} />
);


const openBlockPicker = (state, editor, type) => {
  const picker = window.onegovUrlPicker || window.onegovResourcePicker;

  if (!picker) {
    reportError(new Error(translate('The selection could not be loaded.')));
    return;
  }

  const cursor = editor.getTextCursorPosition();
  const previousId = cursor.prevBlock?.id;
  const nextId = cursor.nextBlock?.id;
  const placeholder = insertOrUpdateBlockForSlashMenu(editor, {
    type: 'paragraph',
  });
  picker.open({
    form: state.form,
    type: type === 'photoAlbum' ? 'photoalbum' : type,
    returnFocus: state.wrapper.querySelector('[contenteditable="true"]'),
    onSelect: (url, label) => {
      const name = label || url.split('/').pop() || url;
      let block;
      if (type === 'internal') {
        block = {
          type: 'paragraph',
          content: [{type: 'link', href: url, content: name}],
        };
      } else if (type === 'photoAlbum') {
        block = {type, props: {url, title: name}};
      } else {
        block = {type, props: {url, name}};
      }
      const current = editor.getBlock(placeholder.id);
      if (current) {
        editor.updateBlock(current, block);
      } else if (previousId && editor.getBlock(previousId)) {
        editor.insertBlocks([block], previousId, 'after');
      } else if (nextId && editor.getBlock(nextId)) {
        editor.insertBlocks([block], nextId, 'before');
      } else {
        editor.insertBlocks([block], editor.document[0], 'before');
      }
      editor.focus();
    },
  });
};


const SourceDialog = ({state, editor, onClose}) => {
  const [source, setSource] = useState(state.textarea.value);
  const [error, setError] = useState('');
  const close = () => {
    onClose();
    editor.focus();
  };

  const apply = () => {
    try {
      const initial = parseInitialHtml(source);
      editor.replaceBlocks(editor.document, initial.blocks);
      state.initial = initial;
      state.sourceOverride = {
        html: source,
        signature: signature(editor.document),
      };
      state.textarea.value = source;
      close();
    } catch (parseError) {
      setError(parseError.message || translate('The HTML could not be parsed.'));
    }
  };

  return (
    <div
      className="onegov-blocknote-dialog-overlay"
      onKeyDown={event => event.key === 'Escape' && close()}
    >
      <section
        aria-labelledby="onegov-blocknote-source-title"
        aria-modal="true"
        className="onegov-blocknote-dialog"
        role="dialog"
      >
        <h2 id="onegov-blocknote-source-title">{translate('HTML')}</h2>
        <textarea
          aria-label={translate('HTML')}
          autoFocus
          onChange={event => setSource(event.target.value)}
          rows="18"
          value={source}
        />
        {error && <p className="onegov-blocknote-error" role="alert">{error}</p>}
        <div className="onegov-blocknote-dialog-actions">
          <button className="button secondary" onClick={close} type="button">
            {translate('Cancel')}
          </button>
          <button className="button" onClick={apply} type="button">
            {translate('Apply')}
          </button>
        </div>
      </section>
    </div>
  );
};


const EditorToolbar = ({editor, onSource}) => {
  return (
    <div className="onegov-blocknote-toolbar" role="toolbar">
      <button
        className="onegov-blocknote-toolbar-button"
        data-onegov-blocknote-control="undo"
        onClick={() => {
          editor.undo();
          editor.focus();
        }}
        onMouseDown={event => event.preventDefault()}
        title={translate('Undo')}
        type="button"
      >↶<span className="show-for-sr">{translate('Undo')}</span></button>
      <button
        className="onegov-blocknote-toolbar-button"
        data-onegov-blocknote-control="redo"
        onClick={() => {
          editor.redo();
          editor.focus();
        }}
        onMouseDown={event => event.preventDefault()}
        title={translate('Redo')}
        type="button"
      >↷<span className="show-for-sr">{translate('Redo')}</span></button>
      <button
        className="onegov-blocknote-toolbar-button"
        data-onegov-blocknote-control="html"
        onClick={onSource}
        title={translate('HTML')}
        type="button"
      >&lt;/&gt;<span className="show-for-sr">{translate('HTML')}</span></button>
    </div>
  );
};


const OneGovBlockNoteEditor = ({state}) => {
  const [sourceOpen, setSourceOpen] = useState(false);
  const editorLanguage = language();
  const aiUrl = state.form?.dataset.blocknoteAiUrl;
  const editor = useCreateBlockNote({
    schema,
    initialContent: state.initial.blocks,
    dictionary: {
      ...dictionaries[editorLanguage],
      ai: aiDictionaries[editorLanguage],
    },
    extensions: aiUrl ? [
      AIExtension({
        agentCursor: {
          color: getComputedStyle(state.wrapper)
            .getPropertyValue('--onegov-primary-color').trim() || '#006fba',
          name: 'AI',
        },
        transport: new DefaultChatTransport({
          api: aiUrl,
          credentials: 'same-origin',
        }),
        documentStateBuilder: buildAddressableAIDocumentState,
      }),
    ] : [],
    uploadFile: (file, blockId) => uploadFile(state, file, blockId),
    tables: {
      headers: true,
      splitCells: true,
      cellBackgroundColor: false,
      cellTextColor: false,
    },
    defaultStyles: true,
    domAttributes: {
      editor: {
        'aria-label': state.label,
        'aria-required': state.textarea.required ? 'true' : 'false',
        'data-onegov-blocknote-editor': '',
      },
    },
  }, []);

  state.editor = editor;
  const onEditorChange = useCallback(() => handleEditorChange(state), [state]);
  const formattingToolbar = useCallback(
    () => <OneGovFormattingToolbar aiEnabled={Boolean(aiUrl)} />,
    [aiUrl],
  );

  useEffect(() => {
    const expand = () => expandEditorToggleHeadings(state.wrapper);
    const observer = new MutationObserver(expand);

    expand();
    observer.observe(state.wrapper, {
      attributeFilter: ['data-show-children'],
      attributes: true,
      childList: true,
      subtree: true,
    });
    return () => observer.disconnect();
  }, [state]);

  const slashItems = useMemo(() => {
    const filtered = getDefaultReactSlashMenuItems(editor)
      .filter(item => item.key !== 'image' && item.key !== 'file')
      .map(item => ({
        ...item,
        onItemClick: restoreEditorFocus(editor, item.onItemClick),
      }));
    const headingGroup = editor.dictionary.slash_menu.heading_2.group;
    [
      {key: 'heading_4', level: 4, Icon: H4Icon},
      {key: 'heading_5', level: 5, Icon: H5Icon},
    ].forEach(({key, level, Icon}) => {
      if (filtered.some(item => item.key === key)) {
        return;
      }
      const item = editor.dictionary.slash_menu[key];
      filtered.push({
        key,
        title: item.title,
        subtext: item.subtext,
        aliases: item.aliases,
        group: headingGroup,
        icon: <Icon />,
        onItemClick: restoreEditorFocus(
          editor,
          () => insertOrUpdateBlockForSlashMenu(editor, {
            type: 'heading',
            props: {level},
          }),
        ),
      });
    });
    const mediaGroup = editor.dictionary.slash_menu.image.group;
    const hasImage = Boolean(
      state.form?.dataset.imageUploadUrl || state.form?.dataset.imageListUrl,
    );
    const hasFile = Boolean(
      state.form?.dataset.fileUploadUrl || state.form?.dataset.fileListUrl,
    ) && !document.body.classList.contains('role-member');
    const hasInternal = Boolean(state.form?.dataset.sitecollectionUrl);
    const hasPhotoAlbum = Boolean(state.form?.dataset.photoalbumListUrl);

    if (hasImage) {
      filtered.push({
        key: 'onegov_image',
        title: translate('Image'),
        subtext: editor.dictionary.slash_menu.image.subtext,
        aliases: ['image', 'bild', 'photo', 'foto', 'immagine'],
        group: mediaGroup,
        icon: <ImageIcon />,
        onItemClick: () => openBlockPicker(state, editor, 'image'),
      });
    }
    if (hasPhotoAlbum) {
      filtered.push({
        key: 'onegov_photo_album',
        title: translate('Photo Album'),
        subtext: translate('Select'),
        aliases: [
          'album', 'photoalbum', 'fotoalbum', 'gallery', 'galerie', 'galleria',
        ],
        group: mediaGroup,
        icon: <PhotoAlbumIcon />,
        onItemClick: () => openBlockPicker(state, editor, 'photoAlbum'),
      });
    }
    if (hasFile) {
      filtered.push({
        key: 'onegov_file',
        title: translate('File'),
        subtext: editor.dictionary.slash_menu.file.subtext,
        aliases: ['file', 'datei', 'document', 'dokument', 'fichier'],
        group: mediaGroup,
        icon: <FileIcon />,
        onItemClick: () => openBlockPicker(state, editor, 'file'),
      });
    }
    if (hasInternal) {
      filtered.push({
        key: 'onegov_internal_link',
        title: translate('Internal Link'),
        subtext: translate('Select'),
        aliases: ['link', 'internal', 'intern', 'lien', 'collegamento'],
        group: mediaGroup,
        icon: <InternalLinkIcon />,
        onItemClick: () => openBlockPicker(state, editor, 'internal'),
      });
    }

    filtered.push({
      key: 'alpha_list',
      title: translate('Alphabetical list'),
      aliases: ['alpha', 'alphabetisch', 'alphabétique', 'alfabetico'],
      group: editor.dictionary.slash_menu.paragraph.group,
      icon: <AlphaIcon />,
      onItemClick: restoreEditorFocus(
        editor,
        () => insertOrUpdateBlockForSlashMenu(editor, {
          type: 'numberedListItem',
          props: {backgroundColor: alphaListMarker, textColor: 'a.'},
        }),
      ),
    });
    filtered.push({
      key: 'edit_note',
      title: translate('Edit note'),
      subtext: translate('Editorial note'),
      aliases: ['note', 'hinweis', 'remarque', 'nota'],
      group: editor.dictionary.slash_menu.paragraph.group,
      icon: <EditNoteIcon />,
      onItemClick: restoreEditorFocus(
        editor,
        () => insertOrUpdateBlockForSlashMenu(editor, {
          type: 'editNote',
        }),
      ),
    });
    if (aiUrl) {
      filtered.push(...getAISlashMenuItems(editor).map(item => ({
        ...item,
        onItemClick: restoreEditorFocus(editor, item.onItemClick),
      })));
    }
    return filtered;
  }, [aiUrl, editor]);

  return (
    <>
      <BlockNoteView
        className="onegov-blocknote-view"
        editor={editor}
        formattingToolbar={false}
        onChange={onEditorChange}
        sideMenu={false}
        slashMenu={false}
        theme="light"
      >
        {aiUrl && <AIMenuController />}
        <FormattingToolbarController
          formattingToolbar={formattingToolbar}
        />
        <SideMenuController sideMenu={OneGovSideMenu} />
        <SuggestionMenuController
          getItems={async query => filterSuggestionItems(slashItems, query)}
          triggerCharacter="/"
        />
      </BlockNoteView>
      <EditorToolbar
        editor={editor}
        onSource={() => setSourceOpen(true)}
      />
      {sourceOpen && (
        <SourceDialog
          editor={editor}
          onClose={() => setSourceOpen(false)}
          state={state}
        />
      )}
    </>
  );
};


const findLabel = textarea => {
  if (textarea.id) {
    const label = document.querySelector(`label[for="${CSS.escape(textarea.id)}"]`);
    if (label) {
      return label.textContent.trim();
    }
  }
  const enclosingLabel = textarea.closest('label');
  if (enclosingLabel) {
    const copy = enclosingLabel.cloneNode(true);
    copy.querySelectorAll('textarea, .onegov-blocknote-wrapper')
      .forEach(element => element.remove());
    return copy.textContent.trim() || translate('Editor');
  }
  return translate('Editor');
};


const mount = textarea => {
  if (!textarea || mountedEditors.has(textarea)) {
    return mountedEditors.get(textarea);
  }

  const wrapper = document.createElement('div');
  wrapper.className = 'onegov-blocknote-wrapper';
  wrapper.dataset.onegovBlocknoteWrapper = '';
  textarea.before(wrapper);
  textarea.classList.add('onegov-blocknote-textarea');
  textarea.setAttribute('aria-hidden', 'true');
  textarea.setAttribute('tabindex', '-1');

  const state = {
    editor: null,
    form: textarea.closest('form'),
    initial: parseInitialHtml(textarea.value),
    label: findLabel(textarea),
    normalizingAlphaLists: false,
    pendingUploads: new Set(),
    root: createRoot(wrapper),
    sourceOverride: null,
    syncRevision: 0,
    textarea,
    wrapper,
  };

  mountedEditors.set(textarea, state);
  registerForm(state);
  state.root.render(<OneGovBlockNoteEditor state={state} />);

  textarea.addEventListener('invalid', () => {
    state.wrapper.querySelector('[contenteditable="true"]')?.focus();
  });

  return state;
};


const mountAll = root => Array.from(
  (root || document).querySelectorAll('textarea.editor'),
).map(mount);


window.OneGovBlockNote = {
  cropImageFile,
  mount,
  mountAll,
};
