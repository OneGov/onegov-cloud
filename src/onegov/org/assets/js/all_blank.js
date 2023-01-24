// vanilla JavaScript
var links = document.links;

function make_target_blank(link) {
  return link.href.includes('storage')
}

for (var i = 0, linksLength = links.length; i < linksLength; i++) {
  if (make_target_blank(links[i])) {
      links[i].target = '_blank';
  }
}