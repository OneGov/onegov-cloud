// vanilla JavaScript
var links = document.links;

function is_external_link(link) {
    if (link.classList.contains('no-icon')) {
        return false;
    }
    if (link.href.startsWith('#')) {
        return false;
    }
    // eslint-disable-next-line no-script-url
    if (link.href.includes('javascript:')) {
        return false;
    }
    if (link.href.includes('mailto:')) {
        return false;
    }
    if (link.href.includes('tel:')) {
        return false;
    }
    return link.hostname !== window.location.hostname;
}

for (var i = 0, linksLength = links.length; i < linksLength; i++) {
    if (is_external_link(links[i])) {
        links[i].target = '_blank';
        const external_link_icon = document.createElement('i');
        external_link_icon.className = 'fas fa-external-link-alt fa-xs';
        const accesibility_info = document.createElement('span');
        accesibility_info.className = 'visually-hidden';
        accesibility_info.textContent = '(External Link)';
        links[i].appendChild(external_link_icon);
        links[i].appendChild(accesibility_info);
    }
}
