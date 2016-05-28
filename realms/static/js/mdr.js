// Init highlight JS
hljs.initHighlightingOnLoad();

function splitInput(str) {
  if (str.slice(0, 3) !== '---') return;

  var matcher = /\n(\.{3}|\-{3})/g;
  var metaEnd = matcher.exec(str);

  return metaEnd && [str.slice(0, metaEnd.index), str.slice(matcher.lastIndex)];
}

/* © 2013 j201
 * https://github.com/j201/meta-marked */


marked.setOptions({
  renderer: new marked.Renderer(),
  gfm: true,
  tables: true,
  breaks: true,
  pedantic: false,
  sanitize: true,
  smartLists: true,
  smartypants: false
});

// Markdown Renderer
var MDR = {
  meta: null,
  md: null,
  sanitize: true, // Override
  renderer: new marked.Renderer(),
  parse: function(md){
    return marked(md, { renderer: this.renderer });
  },
  convert: function(md, sanitize) {
    if (this.sanitize !== null) {
      sanitize = this.sanitize;
    }
    this.md = md;
    try {
      var html = this.parse(this.md);
    } catch(e) {
      return this.md;
    }

    if (sanitize) {
      // Causes some problems with inline styles
      html = html_sanitize(html, function(url) {
        try {
          var prot = decodeURIComponent(url.toString());
        } catch (e) {
          return '';
        }
        if (prot.indexOf('javascript:') === 0) {
          return '';
        }
        return prot;
      }, function(id){
        return id;
      });
    }
    return html;
  },
};

MDR.renderer.table = function(header, body) {
  return '<table class="table table-bordered">\n'
    + '<thead>\n'
    + header
    + '</thead>\n'
    + '<tbody>\n'
    + body
    + '</tbody>\n'
    + '</table>\n';
};
