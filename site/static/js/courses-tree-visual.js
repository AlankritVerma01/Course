// Back Button
const backButton = document.querySelector("#back-button");
backButton.addEventListener("click", () => {
  history.back();
});

/*** Tree Visualisation using the D3 Library ***/

// Padding value to prevent nodes from going out of the screen
const padding = 30;

// Radius of circles
const radius = 30;
// Adjust size of canvas depending on number of objects
const width = Object.keys(data).length <= 30 ? 500 : 1000;
const height = Object.keys(data).length <= 30 ? 500 : 1000;

// Get graphics container
const container = d3.select("#tree-visual-canvas").classed("svg-container", true);

// Get svg graphics object
const svg = container.append("svg")
  .attr("viewBox", `0 0 ${width} ${height}`)
  .classed("svg-content-responsive", true);

// Create d3 simulation
const simulation = d3.forceSimulation()
  .force("link", d3.forceLink().id(d => d.id).distance(100)) // Linked objects pull towards each other
  .force("collide", d3.forceCollide(radius*1.8)) // Objects have collision plus "invisible" boundary
  .force("center", d3.forceCenter(width / 2, height / 2)); // Objects gather in center


// Arrow marker definition
const arrowSize = 8;
svg.append("svg:defs").selectAll("marker")
  .data(["arrow"])
  .join("svg:marker")
  .attr("id", String)
  .attr("viewBox", "0 -5 10 10")
  .attr("refX", arrowSize + radius + arrowSize)
  .attr("refY", 0)
  .attr("markerWidth", arrowSize)
  .attr("markerHeight", arrowSize)
  .attr("orient", "auto")
  .append("svg:path")
  .attr("d", "M0,-5L10,0L0,5")
  .attr("class", "arrow");

// Create data objects for graphical representation of tree
const nodes = Object.keys(data).map(key => ({
  id: key
}));
const links = nodes.flatMap(node => (data[node.id] || []).map(target => ({ source: node.id, target })));

// List of root nodes of tree
const headNodes = nodes.filter(node => links.every(link => link.target !== node.id));

// Link between nodes definition
const link = svg.append("g")
  .selectAll("line")
  .data(links)
  .join("line")
  .attr("class", "link")
  .attr("marker-end", "url(#arrow)");

// Create node objects consisting of circle and text
bubbles = svg.selectAll('.bubble')
  .data(nodes)
  .enter()
  .append('g')
  .classed('bubble', true)
  .on("click", d => {
    window.location.href = `course/${d.target.__data__.id}`;
  })
  .call(d3.drag()
    .on("start", dragstarted)
    .on("drag", dragged)
    .on("end", dragended));

// Circle objects for nodes 
circles = bubbles.append('circle')
  .attr("r", radius)
  .style("fill", d => {
    // Highlight head nodes in red
    return headNodes.some(headNode => headNode.id === d.id) ? "red" : "#ccc";
  });

// Text objects for nodes
texts = bubbles.append('text')
  .attr('text-anchor', 'middle')
  .attr('alignment-baseline', 'middle')
  .style('font-size', radius * 0.4 + 'px')
  .text(d => d.id);

// Add nodes to simulation
simulation.nodes(nodes)
  .on("tick", ticked);

// Link objects together in simulation
simulation.force("link")
  .links(links);
  
// Function for moving objects per tick
function ticked() {
  link
    .attr("x1", d => d.source.x)
    .attr("y1", d => d.source.y)
    .attr("x2", d => d.target.x)
    .attr("y2", d => d.target.y);

  circles
    .attr("cx", d => d.x = Math.max(padding, Math.min(width - padding, d.x)))
    .attr("cy", d => d.y = Math.max(padding, Math.min(height - padding, d.y)));

  texts
    .attr("x", d => d.x)
    .attr("y", d => d.y);
}

// Functions for node dragging event
function dragstarted(event, d) {
  if (!event.active) simulation.alphaTarget(0.3).restart();
  d.fx = d.x;
  d.fy = d.y;
}

function dragged(event, d) {
  d.fx = event.x;
  d.fy = event.y;
}

function dragended(event, d) {
  if (!event.active) simulation.alphaTarget(0);
  d.fx = null;
  d.fy = null;
}
