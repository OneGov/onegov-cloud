const orgchartDiv = document.querySelector('.orgchart');
const apiUrl = orgchartDiv.dataset.url;

fetch(apiUrl)
    .then((response) => {
        console.log('Raw response:', response);
        return response.json();
    })
    .then((data) => {
        if (!data.tree || !data.tree[0]) {
            console.error('Invalid data structure:', data);
            return;
        }
        const hierarchicalData = data.tree[0];
        const flattenedData = getFlattenedData(hierarchicalData);
        new d3.OrgChart()
            .nodeWidth((node) => 200)
            .nodeHeight((node) => 100)
            .nodeContent((node) => {
                const hasLongWord = node.data.name.split(' ').some(word => word.length > 15);
                const hyphenClass = hasLongWord ? ' hyphens' : '';
                return `
                    <a href="${node.data.url}">
                        <div class="d3-orgchart-node ${hyphenClass}" style="width:${node.width}px;height:${node.height}px">
                            <span>${node.data.name}</span>
                        </div>
                    </a>
                `;
            })
            .container('.chart-container').data(flattenedData).render();
    })
    .catch((error) => {
        console.error('Error:', error);
    });

function getFlattenedData(dataHierarchy) {
    const descendants = d3.hierarchy(dataHierarchy).descendants();
    descendants.forEach((d, i) => {
        d.id = d.id || 'id' + i;
    });
    return descendants
        .map((d, i) => [d.parent?.data?.id, d.data])
        .map(([parentId, data]) => {
            const copy = { ...data };
            delete copy.children;
            return { ...copy, ...{ parentId } };
        });
}