import { Editor } from '@tiptap/core';
import { StarterKit } from '@tiptap/starter-kit'
import { BubbleMenu } from '@tiptap/extension-bubble-menu'
// create a simple namespace to export the symbols we need as globals
window.tiptap = {
    Editor: Editor,
    BubbleMenu: BubbleMenu,
    StarterKit: StarterKit
};
