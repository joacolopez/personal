# Fact: tiponodo
# Verifica condiciones de vinculos.


# Proyectos Especiales.
# Gerencia Tecnologia.
# 02/05/2018
# path: /usr/lib/ruby/1.8/facter/vinculo.rb

##############################################################################
# IMPORTANTE!!!!!!!!! Este script tiene dependiencias.                       #
#                                                                            #
# Archivo: /usr/lib/ruby/1.8/inifile.rb                                      #
# MD5: 892875a7e5c113e0eefeaf54493827be                                      #
#                                                                            #
# Referencia: [[https://rubygems.org/gems/inifile/versions/2.0.2]]           #
#                                                                            #
#                                                                            #
#                                                                            #
#                                                                            #
##############################################################################


require 'inifile'
 
if File.exist? '/etc/credicoop_info_nodo.ini'
	ini_file = IniFile.load("/etc/credicoop_info_nodo.ini")
	ini_file.each do |section, parameter, value|
		#puts "#{parameter} = #{value} [in section - #{section}]"
		Facter.add("#{section}_#{parameter}") do
			setcode do
				"#{value}"
			end
		end
	end
end

