<?xml version='1.0' encoding='utf-8'?>
<!DOCTYPE resources PUBLIC "-//NISO//DTD resource 2005-1//EN" "http://www.daisy.org/z3986/2005/resource-2005-1.dtd">
<!-- file and contents not yet tested -->
<resources xmlns="http://www.daisy.org/z3986/2005/resource/" version="2005-1">
  <scope nsuri="http://www.daisy.org/z3986/2005/ncx/">
    <nodeSet id="ns006" select="//smilCustomTest[@bookStruct='PAGE_NUMBER']">
      <resource xml:lang="en" id="r1">
        <text>Page</text>
      </resource>
    </nodeSet>
    <nodeSet id="ns007" select="//smilCustomTest[@bookStruct='PAGE_NUMBER']">
      <resource xml:lang="en" id="r2">
        <text>Header</text>
      </resource>
    </nodeSet>
  </scope>

  <scope nsuri="http://www.w3.org/2001/SMIL20/">   
    <nodeSet id="esns006" select="//seq[@class='pagenum']">
      <resource xml:lang="en" id="r3">
        <text>Page</text>
      </resource>
    </nodeSet>
  </scope>

  <scope nsuri="http://www.daisy.org/z3986/2005/dtbook/"> 
    <nodeSet id="ns015" select="//sidebar[@render='optional']">
      <resource xml:lang="en" id="r4">
        <text>Optional sidebar</text>
      </resource>
    </nodeSet>

    <nodeSet id="ns016" select="//table">
      <resource xml:lang="en" id="r5">
        <text>Table</text>
      </resource>
    </nodeSet>
  </scope>
</resources>



<!--     <nodeSet id="ns001" select="//smilCustomTest[@bookStruct='PAGE_NUMBER']"> -->
<!--       <resource xml:lang="en" id="r001"> -->
<!--         <text>page</text> -->
<!--         <audio src="res_en.mp3" clipBegin="0.2s" clipEnd="0.4s"/> -->
<!--       </resource> -->
<!--     </nodeSet>            -->
<!--     <nodeSet id="ns002" select="//smilCustomTest[@id='foo']"> -->
<!--       <resource xml:lang="en" id="r002"> -->
<!--         <text>verse</text> -->
<!--         <audio src="res_en.mp3" clipBegin="0.8s" clipEnd="1.0s"/> -->
<!--       </resource>       -->
<!--     </nodeSet>          -->
<!--     <nodeSet id="ns003" select="//navPoint[@class='chapter']"> -->
<!--       <resource xml:lang="en" id="r003">  -->
<!--         <text>chapter</text> -->
<!--         <audio src="chapter.mp3" clipBegin="2.8s" clipEnd="3.0s"/>  -->
<!--         <img src="chapter.png" />  -->
<!--       </resource >  -->
<!--     </nodeSet>    -->
<!--   </scope> -->
  
<!--   <scope nsuri="http://www.daisy.org/z3986/2005/dtbook/"> -->
<!--     <nodeSet id="ns004" select="//prodnote[@render='optional']"> -->
<!--       <resource xml:lang="en" id="r004"> -->
<!--         <text>optional producers note</text> -->
<!--         <audio src="res_en.mp3" clipBegin="2.8s" clipEnd="3.0s"/> -->
<!--       </resource>       -->
<!--     </nodeSet>             -->
<!--     <nodeSet id="ns005" select="//td"> -->
<!--       <resource xml:lang="en" id="r005"> -->
<!--         <text>table cell</text> -->
<!--         <audio src="res_en.mp3" clipBegin="1.2s" clipEnd="1.4s"/> -->
<!--       </resource> -->
<!--     </nodeSet>            -->
