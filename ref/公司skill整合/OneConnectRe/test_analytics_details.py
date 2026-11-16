from pathlib import Path
p=Path('tests/analytics.test.cjs');s=p.read_text(encoding='utf8');s=s.replace("console.log('analytics mapping PASS');", "assert.equal(w.oneConnectHost.events()[1].detail.level,1);assert.equal(w.oneConnectHost.events()[5].detail.reason,'timeout');console.log('analytics mapping PASS');");p.write_text(s,encoding='utf8')
