// Acesse: https://sigaa.unb.br/sigaa/public/turmas/listar.jsf
// Para cada departamento (FGA, MAT, FIS, etc.):
//   1. Filtre pelo departamento e período 2026.1, clique em Buscar
//   2. Cole esse script no console e pressione Enter
//   3. Repita para os demais departamentos
// Ao final, rode: copy(JSON.stringify(__turmas__, null, 2))
// e salve o resultado como data.json

if (!window.__turmas__) window.__turmas__ = [];

var linhas = document.querySelectorAll('#turmasAbertas tbody tr');
var materiaAtual = '';
var adicionadas = 0;

for (const linha of linhas) {
  if (linha.classList.contains('agrupador')) {
    materiaAtual = linha.innerText.trim();
  } else {
    var cols = linha.innerText.split('\t').map(x => x.trim()).filter(x => x !== '');
    if (cols.length >= 4) {
      var turma = {
        materia: materiaAtual,
        turma: cols[0],
        professor: cols[2],
        horario: cols[3],
        link: ""
      };

      // evita duplicatas
      var existe = window.__turmas__.some(
        t => t.materia === turma.materia && t.turma === turma.turma
      );

      if (!existe) {
        window.__turmas__.push(turma);
        adicionadas++;
      }
    }
  }
}

window.__turmas__.sort((a, b) => {
  if (a.materia !== b.materia) return a.materia.localeCompare(b.materia);
  return a.turma.localeCompare(b.turma);
});

console.log(`✅ ${adicionadas} turmas adicionadas. Total acumulado: ${window.__turmas__.length}`);
console.log('Quando terminar todos os departamentos, rode:');
console.log('  copy(JSON.stringify(__turmas__, null, 2))');
