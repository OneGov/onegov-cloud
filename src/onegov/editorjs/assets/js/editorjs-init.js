function base64EncodeUnicode(str) {
    // First we escape the string using encodeURIComponent to get the UTF-8 encoding of the characters,
    // then we convert the percent encodings into raw bytes, and finally feed it to btoa() function.
    utf8Bytes = encodeURIComponent(str).replace(/%([0-9A-F]{2})/g, function(match, p1) {
            return String.fromCharCode('0x' + p1);
    });

    return btoa(utf8Bytes);
}

$('.editorjs').each(function () {
    var el = $(this);
    console.log(this);
    let wrapper = $('<div/>', {id: `id-${el.attr('id')}`, "class": 'editorjs-wrapper'})
    el.after(wrapper);

    let form = el.closest('form')
    let fileUploadUrl = form.data('file-upload-url')
    let imageUploadUrl = form.data('image-upload-url')

    let initialData = el.val() && JSON.parse(atob(el.val())) || {}

    let config = {
        holder: `id-${el.attr('id')}`,
        tools: {
            list: {
                class: List,
                inlineToolbar: true
            },
            header: {
              class: Header,
              inlineToolbar : true
            },
            embed: {
                class: Embed,
                services: {
                  youtube: true,
                  coub: true
                }
            },
            code: {
                class: CodeTool
            },
            raw: {
                class: RawTool
            },
            image: {
                class: ImageTool,
                config: {
                    endpoints: {
                      byFile: '', // Your backend file uploader endpoint
                      byUrl: '', // Your endpoint that provides uploading by Url
                    }
                }
            }
      },
        data: initialData,
        placeholder: el.attr('placeholder'),
        readOnly: el.attr('disabled') && true || false,
        onReady: () => {
          console.log('Editor.js is ready to work!')
       },
       onChange: () => {
            console.log('Now I know that Editor\'s content changed!')
        }
    }
    const editor = new EditorJS(config)
     wrapper.mouseleave(function () {
         console.log(editor.render())
        editor.save().then((outputData) => {
            if (config.readOnly) return;
            let text = JSON.stringify(outputData);
            console.log(text);
            text = base64EncodeUnicode(text);
            el.val(text);
        }).catch((error) => {
          console.log('Saving failed: ', error)
        });
    })
})
