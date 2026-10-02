# Capturas

Telas da aplicacao em modo de demonstracao (`make dev-frontend`), redimensionadas
para 1920px de largura. Sao as imagens da historia e da galeria do README da raiz.

| Arquivo | Tela |
| ------- | ---- |
| `carrossel.gif` | Tour animado pelas telas abaixo, usado no topo do README |
| `01-site-hero.png` | Site: hero e previa do painel |
| `02-site-numeros.png` | Site: numeros e inicio dos recursos |
| `03-site-recursos.png` | Site: os seis recursos |
| `04-site-como-funciona.png` | Site: como funciona e perguntas frequentes |
| `05-site-chamada-final.png` | Site: perguntas, chamada final e rodape |
| `06-login.png` | Login |
| `07-painel-visao-geral.png` | Painel: banner do dia e indicadores |
| `08-painel-graficos.png` | Painel: pedidos por dia e por status |
| `09-painel-operacao.png` | Painel: reposicao, taxa de entrega, saude do estoque e pedidos recentes |

Para refazer o carrossel depois de trocar as capturas (precisa de `ffmpeg`):

```bash
cd docs/screenshots
frames=(01-site-hero 03-site-recursos 04-site-como-funciona 05-site-chamada-final \
        06-login 07-painel-visao-geral 08-painel-graficos 09-painel-operacao)
inputs=(); filt=""; n=${#frames[@]}
for i in $(seq 0 $((n-1))); do
  inputs+=(-loop 1 -t 3.5 -i "${frames[$i]}.png")   # bash: indice a partir de 0
  filt+="[$i:v]scale=1920:-1,pad=1920:940:0:(940-ih)/2:color=0xf4f5fa,scale=1100:-1:flags=lanczos,format=yuv420p,setsar=1,fps=12[v$i];"
done
prev=v0
for i in $(seq 1 $((n-1))); do
  filt+="[$prev][v$i]xfade=transition=slideleft:duration=0.5:offset=$((i*3))[x$i];"; prev=x$i
done
filt+="[$prev]split[a][b];[a]palettegen=max_colors=192:stats_mode=diff[p];[b][p]paletteuse=dither=sierra2_4a:diff_mode=rectangle"
ffmpeg -y "${inputs[@]}" -filter_complex "$filt" -loop 0 carrossel.gif
```
