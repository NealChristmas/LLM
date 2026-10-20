param([string]$SvgPath,[string]$PngPath)
Add-Type -AssemblyName System.Drawing
[xml]$svgDoc=Get-Content -LiteralPath $SvgPath -Raw -Encoding UTF8
$bmp=New-Object System.Drawing.Bitmap(2260,1720)
$g=[System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode=[System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$g.TextRenderingHint=[System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
$g.Clear([System.Drawing.Color]::White)
$normal=New-Object System.Drawing.Font('Microsoft YaHei',22,[System.Drawing.FontStyle]::Regular,[System.Drawing.GraphicsUnit]::Pixel)
$heading=New-Object System.Drawing.Font('Microsoft YaHei',25,[System.Drawing.FontStyle]::Bold,[System.Drawing.GraphicsUnit]::Pixel)
$fmt=New-Object System.Drawing.StringFormat
$fmt.Alignment=[System.Drawing.StringAlignment]::Center
$fmt.LineAlignment=[System.Drawing.StringAlignment]::Near
foreach($el in $svgDoc.DocumentElement.ChildNodes){
 if($el.LocalName -eq 'rect' -and $el.GetAttribute('rx')){
  $x=[single]$el.x;$y=[single]$el.y;$w=[single]$el.width;$h=[single]$el.height;$radius=22
  $shape=New-Object System.Drawing.Drawing2D.GraphicsPath
  $shape.AddArc($x,$y,44,44,180,90);$shape.AddArc(($x+$w-44),$y,44,44,270,90);$shape.AddArc(($x+$w-44),($y+$h-44),44,44,0,90);$shape.AddArc($x,($y+$h-44),44,44,90,90);$shape.CloseFigure()
  $brush=New-Object System.Drawing.SolidBrush([System.Drawing.ColorTranslator]::FromHtml($el.fill))
  $pen=New-Object System.Drawing.Pen([System.Drawing.ColorTranslator]::FromHtml($el.stroke),1.5)
  $g.FillPath($brush,$shape);$g.DrawPath($pen,$shape);$brush.Dispose();$pen.Dispose();$shape.Dispose()
 }elseif($el.LocalName -eq 'path' -and $el.GetAttribute('class') -eq 'edge'){
  $nums=[regex]::Matches($el.d,'-?\d+(?:\.\d+)?')
  $pts=New-Object 'System.Collections.Generic.List[System.Drawing.PointF]'
  for($i=0;$i -lt $nums.Count;$i+=2){$pts.Add((New-Object System.Drawing.PointF([single]$nums[$i].Value,[single]$nums[$i+1].Value)))}
  $pen=New-Object System.Drawing.Pen([System.Drawing.ColorTranslator]::FromHtml('#9ca3a7'),1.8)
  $cap=New-Object System.Drawing.Drawing2D.AdjustableArrowCap(4,5)
  $pen.CustomEndCap=$cap;$g.DrawLines($pen,$pts.ToArray());$pen.Dispose();$cap.Dispose()
 }elseif($el.LocalName -eq 'text'){
  $font=$normal;if($el.GetAttribute('class') -eq 'head'){$font=$heading}
  $brush=New-Object System.Drawing.SolidBrush([System.Drawing.ColorTranslator]::FromHtml('#135b96'))
  $rect=New-Object System.Drawing.RectangleF(([single]$el.x-1100),([single]$el.y-$font.Size*1.08),2200,40)
  $g.DrawString($el.InnerText,$font,$brush,$rect,$fmt);$brush.Dispose()
 }
}
$bmp.Save($PngPath,[System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose();$bmp.Dispose();$normal.Dispose();$heading.Dispose();$fmt.Dispose()
Write-Output 'Local SVG raster preview saved.'
