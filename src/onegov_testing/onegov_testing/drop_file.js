var element = arguments[0],
  offsetX = arguments[1],
  offsetY = arguments[2],
  doc = element.ownerDocument || document;

for (var i = 0; ;) {
  var box = element.getBoundingClientRect(),
    clientX = box.left + (offsetX || (box.width / 2)),
    clientY = box.top + (offsetY || (box.height / 2)),
    target = doc.elementFromPoint(clientX, clientY);
  
  if (target && element.contains(target))
      break;
  
  if (++i > 1) {
    var ex = new Error('Element not interactable');
    ex.code = 15;
    throw ex;
  }
  
  element.scrollIntoView({behavior: 'instant', block: 'center', inline: 'center'});
}

var input = doc.createElement('INPUT');
input.setAttribute('type', 'file');
input.setAttribute('style', 'position:fixed;z-index:2147483647;left:0;top:0;');
input.onchange = function (ev) {
  input.parentElement.removeChild(input);
  ev.stopPropagation();

  var dataTransfer = {
    constructor   : DataTransfer,
    effectAllowed : 'all',
    dropEffect    : 'none',
    types         : [ 'Files' ],
    files         : input.files,
    setData       : function setData(){},
    getData       : function getData(){},
    clearData     : function clearData(){},
    setDragImage  : function setDragImage(){}
  };

  if (window.DataTransferItemList) {
    dataTransfer.items = Object.setPrototypeOf( [ {
      constructor : DataTransferItem,
      kind        : 'file',
      type        : dataTransfer.files[0].type,
      getAsFile   : function getAsFile () { return dataTransfer.files[0] },
      getAsString : function getAsString (callback) {
        var reader = new FileReader();
        reader.onload = function(ev) { callback(ev.target.result) };
        reader.readAsText(dataTransfer.files[0]);
      }
    } ], {
      constructor : DataTransferItemList,
      add    : function add(){},
      clear  : function clear(){},
      remove : function remove(){}
    } );
  }
  
  ['dragenter', 'dragover', 'drop'].forEach(function (type) {
    var event = doc.createEvent('DragEvent');
    event.initMouseEvent(type, true, true, doc.defaultView, 0, 0, 0, clientX, clientY, false, false, false, false, 0, null);
    
    Object.setPrototypeOf(event, null);
    event.dataTransfer = dataTransfer;
    Object.setPrototypeOf(event, DragEvent.prototype);
    
    target.dispatchEvent(event);
  });
};

doc.documentElement.appendChild(input);
input.getBoundingClientRect(); /* force reflow */
return input;
