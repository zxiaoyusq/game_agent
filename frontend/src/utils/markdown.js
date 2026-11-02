// 将知识库 Markdown 转成安全的阅读 HTML。原文先统一转义，避免其中的 HTML 被执行。
function escapeHtml(value) {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

// 行内格式只生成固定标签。相对路径由调用方解析成知识库附件，再次检查协议后输出。
function renderInline(value, options = {}) {
  const safeUrl = (url, image = false) => {
    const allowed = image ? /^(https?:\/\/|\/api\/knowledge\/)/i : /^(https?:\/\/|mailto:|\/api\/knowledge\/)/i
    // 工作流调用方可显式开放自己的产物接口，知识库的默认允许范围保持不变。
    const internalAllowed = (options.internalPathPrefixes || []).some((prefix) => url.startsWith(prefix))
    if (allowed.test(url) || internalAllowed) return url
    // 禁止协议相对地址、自定义协议和绝对路径进入相对附件解析器。
    if (/^(?:[a-z][a-z\d+.-]*:|\/|\\)/i.test(url)) return ''
    const resolved = options.resolveRelativeUrl?.(url, image)
    const resolvedAllowed = resolved && (/^\/api\/knowledge\//.test(resolved)
      || (options.internalPathPrefixes || []).some((prefix) => resolved.startsWith(prefix)))
    return resolvedAllowed ? escapeHtml(resolved) : ''
  }
  let text = escapeHtml(value)
  const code = []
  text = text.replace(/`([^`]+)`/g, (_, content) => {
    code.push(`<code>${content}</code>`)
    return `\u0000${code.length - 1}\u0000`
  })
  text = text.replace(/!\[([^\]]*)\]\(([^)\s]+)(?:\s+"([^"]*)")?\)/g, (match, alt, url, title) => {
    const href = safeUrl(url, true)
    if (!href) return alt
    const titleAttr = title ? ` title="${title}"` : ''
    return `<img src="${href}" alt="${alt}"${titleAttr} loading="lazy">`
  })
  text = text.replace(/\[([^\]]+)\]\(([^)\s]+)(?:\s+"([^"]*)")?\)/g, (match, label, url, title) => {
    const href = safeUrl(url)
    if (!href) return label
    const titleAttr = title ? ` title="${title}"` : ''
    const external = /^https?:\/\//i.test(url)
      ? ' target="_blank" rel="noopener noreferrer"'
      : ''
    return `<a href="${href}"${titleAttr}${external}>${label}</a>`
  })
  text = text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/__(.+?)__/g, '<strong>$1</strong>')
    .replace(/~~(.+?)~~/g, '<del>$1</del>')
    .replace(/(^|[^*])\*([^*\n]+)\*/g, '$1<em>$2</em>')
    .replace(/(^|[^_])_([^_\n]+)_/g, '$1<em>$2</em>')
  return text.replace(/\u0000(\d+)\u0000/g, (_, index) => code[Number(index)])
}

// 识别 Markdown 表格的分隔行，并保留列对齐设置。
function parseTableDivider(line) {
  const cells = line.trim().replace(/^\||\|$/g, '').split('|').map((cell) => cell.trim())
  if (!cells.length || !cells.every((cell) => /^:?-{3,}:?$/.test(cell))) return null
  return cells.map((cell) => cell.startsWith(':')
    ? (cell.endsWith(':') ? 'center' : 'left')
    : (cell.endsWith(':') ? 'right' : ''))
}

// 按块解析标题、列表、引用、代码块和表格，普通段落保留换行。
export function renderMarkdown(source, options = {}) {
  // 为每个块共用同一套附件解析规则，避免表格与正文的链接行为不同。
  const inline = (value) => renderInline(value, options)
  const lines = source.replace(/\r\n?/g, '\n').split('\n')
  const blocks = []
  let index = 0

  while (index < lines.length) {
    const line = lines[index]
    if (!line.trim()) {
      index += 1
      continue
    }

    if (/^\s*(```|~~~)/.test(line)) {
      const marker = line.trim().slice(0, 3)
      const language = line.trim().slice(3).trim().split(/\s+/)[0]
      const code = []
      index += 1
      while (index < lines.length && !lines[index].trim().startsWith(marker)) {
        code.push(lines[index])
        index += 1
      }
      index += index < lines.length ? 1 : 0
      const classAttr = /^[\w+-]+$/.test(language) ? ` class="language-${language}"` : ''
      blocks.push(`<pre><code${classAttr}>${escapeHtml(code.join('\n'))}</code></pre>`)
      continue
    }

    if (index + 1 < lines.length && line.includes('|')) {
      const alignments = parseTableDivider(lines[index + 1])
      if (alignments) {
        const splitRow = (row) => row.trim().replace(/^\||\|$/g, '').split('|')
        const header = splitRow(line)
        const bodyRows = []
        let rowIndex = index + 2
        while (rowIndex < lines.length && lines[rowIndex].includes('|')) {
          bodyRows.push(splitRow(lines[rowIndex]))
          rowIndex += 1
        }
        const cell = (content, tag, column) => {
          const align = alignments[column]
          const style = align ? ` style="text-align:${align}"` : ''
          return `<${tag}${style}>${inline((content || '').trim())}</${tag}>`
        }
        const head = `<thead><tr>${header.map((value, column) => cell(value, 'th', column)).join('')}</tr></thead>`
        const body = bodyRows.length
          ? `<tbody>${bodyRows.map((row) => `<tr>${header.map((_, column) => cell(row[column], 'td', column)).join('')}</tr>`).join('')}</tbody>`
          : ''
        blocks.push(`<div class="md-table-wrap"><table>${head}${body}</table></div>`)
        index = rowIndex
        continue
      }
    }

    const heading = line.match(/^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$/)
    if (heading) {
      const level = heading[1].length
      blocks.push(`<h${level}>${inline(heading[2])}</h${level}>`)
      index += 1
      continue
    }
    if (/^\s*((\*\s*){3,}|(-\s*){3,}|(_\s*){3,})$/.test(line)) {
      blocks.push('<hr>')
      index += 1
      continue
    }
    if (/^\s*>/.test(line)) {
      const quote = []
      while (index < lines.length && /^\s*>/.test(lines[index])) {
        quote.push(lines[index].replace(/^\s*>\s?/, ''))
        index += 1
      }
      blocks.push(`<blockquote>${quote.map(inline).join('<br>')}</blockquote>`)
      continue
    }

    const listMatch = line.match(/^\s*(?:([-+*])\s+|(\d+)[.)]\s+)(.*)$/)
    if (listMatch) {
      const ordered = Boolean(listMatch[2])
      const tag = ordered ? 'ol' : 'ul'
      const items = []
      while (index < lines.length) {
        const item = lines[index].match(/^\s*(?:([-+*])\s+|(\d+)[.)]\s+)(.*)$/)
        if (!item || Boolean(item[2]) !== ordered) break
        items.push(`<li>${inline(item[3])}</li>`)
        index += 1
      }
      blocks.push(`<${tag}>${items.join('')}</${tag}>`)
      continue
    }

    const paragraph = []
    while (index < lines.length && lines[index].trim()) {
      if (paragraph.length && (/^\s{0,3}#{1,6}\s/.test(lines[index])
        || /^\s*(?:```|~~~|>|[-+*]\s+|\d+[.)]\s+)/.test(lines[index]))) break
      paragraph.push(lines[index].trim())
      index += 1
    }
    blocks.push(`<p>${paragraph.map(inline).join('<br>')}</p>`)
  }

  return blocks.join('\n')
}
